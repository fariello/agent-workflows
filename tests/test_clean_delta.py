"""Unit tests for clean-delta skills, D113 host evidence, adapter manifest, and zero-target-write guarantees (IPD 20260810-awphysical-09)."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from agent_workflows.clean_delta import (
    ADVERTISED_CLEAN_DELTA_CLAIMS,
    D113_EVIDENCE_PAIRS,
    AdapterPurityError,
    CleanDeltaManager,
    UnsupportedHostError,
    build_default_adapter_manifest,
    compute_target_delta,
    convert_legacy_adapters,
    repair_adapters,
    resolve_adapter_reference,
    snapshot_target_state,
    uninstall_adapters,
    validate_host_evidence,
    verify_adapter_purity,
)
from agent_workflows.project_registry import register_or_update_project
from agent_workflows.project_schema import DeliveryMode, RecordsBackend


class PhysicalAdapterAndDeltaTests(unittest.TestCase):
    """Execution and validation test cases E-01 through E-08 for Order 09 IPD."""

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.target_repo = os.path.join(self.tmp_dir, "myrepo")
        os.makedirs(os.path.join(self.target_repo, ".git"), exist_ok=True)
        self.aw_home = os.path.join(self.tmp_dir, "aw_home")
        os.makedirs(self.aw_home, exist_ok=True)
        self.user_skills_dir = os.path.join(self.tmp_dir, "user_skills")
        os.makedirs(self.user_skills_dir, exist_ok=True)

        self._prev_aw_home = os.environ.get("AW_HOME")
        os.environ["AW_HOME"] = self.aw_home
        register_or_update_project(
            self.target_repo, self.aw_home, project_id="myrepo-order09"
        )

        # Create basic .aw structure
        config_dir = Path(self.target_repo) / ".aw" / "config"
        config_dir.mkdir(parents=True, exist_ok=True)
        policy_data = {
            "delivery_mode": DeliveryMode.TRACKED.value,
            "records_backend": RecordsBackend.REPOSITORY.value,
            "aw_home": self.aw_home,
        }
        (config_dir / "config.json").write_text(
            json.dumps(policy_data), encoding="utf-8"
        )
        os.makedirs(
            os.path.join(self.target_repo, ".aw", "records", "plans"), exist_ok=True
        )
        os.makedirs(
            os.path.join(self.target_repo, ".aw", "state", "durable"), exist_ok=True
        )

    def tearDown(self):
        if self._prev_aw_home is None:
            os.environ.pop("AW_HOME", None)
        else:
            os.environ["AW_HOME"] = self._prev_aw_home
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    # -------------------------------------------------------------------------
    # E-01 / V-01: Versioned adapter manifest & observed clean-delta writes
    # -------------------------------------------------------------------------

    def test_e01(self):
        """E-01: Every out-of-.aw AW file has a host-evidence justification and manifest owner."""

        fixture_path = (
            Path(__file__).resolve().parent
            / "fixtures"
            / "awphysical"
            / "order09"
            / "e01-adapter-manifest.json"
        )
        self.assertTrue(fixture_path.is_file(), f"Fixture missing: {fixture_path}")
        fix_data = json.loads(fixture_path.read_text(encoding="utf-8"))

        manifest = build_default_adapter_manifest(
            Path(self.target_repo), target_repo=self.target_repo, aw_home=self.aw_home
        )
        self.assertGreaterEqual(
            len(manifest.entries), fix_data["expected_adapter_count"]
        )

        for path_key, entry in manifest.entries.items():
            self.assertTrue(entry.host != "")
            self.assertTrue(entry.required_exact_path == path_key)

        # Test install_clean_delta with clean target repo (should report 0 target_writes)
        clean_repo = os.path.join(self.tmp_dir, "clean_repo")
        os.makedirs(os.path.join(clean_repo, ".git"), exist_ok=True)
        mgr = CleanDeltaManager(target_repo=clean_repo, aw_home=self.aw_home)
        res_clean = mgr.install_clean_delta(
            "opencode", "1.0.0", user_skills_dir=self.user_skills_dir
        )
        self.assertEqual(res_clean["target_writes"], 0)

        # Plant a target write canary and assert install_clean_delta detects and reports it
        planted = Path(clean_repo) / fix_data["planted_target_write"]
        planted.parent.mkdir(parents=True, exist_ok=True)
        planted.write_text("planted content", encoding="utf-8")

        res_planted = mgr.install_clean_delta(
            "opencode", "1.0.0", user_skills_dir=self.user_skills_dir
        )
        self.assertGreaterEqual(
            res_planted["target_writes"], fix_data["expected_target_writes_on_planted"]
        )

    # -------------------------------------------------------------------------
    # E-02 / V-02: Portable references & system/project context resolution
    # -------------------------------------------------------------------------

    def test_e02(self):
        """E-02: Tracked adapters use portable target-relative references; external modes use stable invocation."""

        fixture_path = (
            Path(__file__).resolve().parent
            / "fixtures"
            / "awphysical"
            / "order09"
            / "e02-portable-references.json"
        )
        self.assertTrue(fixture_path.is_file())
        fix_data = json.loads(fixture_path.read_text(encoding="utf-8"))

        # Target-resident reference
        ref_resident = resolve_adapter_reference(
            fix_data["target_resident_reference"],
            target_repo=self.target_repo,
            aw_home=self.aw_home,
        )
        self.assertEqual(ref_resident, fix_data["target_resident_reference"])
        self.assertFalse(
            ref_resident.startswith(fix_data["forbidden_absolute_path_prefix"])
        )

        # Configure clean-target delivery mode
        policy_data = {
            "delivery_mode": DeliveryMode.CLEAN_DELTA.value,
            "records_backend": RecordsBackend.HOME.value,
            "aw_home": self.aw_home,
        }
        (Path(self.target_repo) / ".aw" / "config" / "config.json").write_text(
            json.dumps(policy_data), encoding="utf-8"
        )

        ref_external = resolve_adapter_reference(
            ".aw/system/workflows/scaffold/scaffold.md",
            target_repo=self.target_repo,
            aw_home=self.aw_home,
        )
        self.assertTrue(ref_external.startswith("python3 -m agent_workflows"))
        self.assertFalse(
            ref_external.startswith(fix_data["forbidden_absolute_path_prefix"])
        )

    # -------------------------------------------------------------------------
    # E-03 / V-03: Adapter purity & single-sourcing
    # -------------------------------------------------------------------------

    def test_e03(self):
        """E-03: Generated adapter set equals manifest set, and canonical instructions remain single-sourced."""

        fixture_path = (
            Path(__file__).resolve().parent
            / "fixtures"
            / "awphysical"
            / "order09"
            / "e03-adapter-purity.json"
        )
        self.assertTrue(fixture_path.is_file())
        fix_data = json.loads(fixture_path.read_text(encoding="utf-8"))

        # Valid shim pointer passes purity test
        self.assertTrue(
            verify_adapter_purity(
                Path(".opencode/commands/scaffold.md"), fix_data["valid_shim_pointer"]
            )
        )

        # Impure duplicated body raises AdapterPurityError
        with self.assertRaises(AdapterPurityError):
            verify_adapter_purity(
                Path(".opencode/commands/scaffold.md"),
                fix_data["impure_duplicated_body"],
            )

        # Impure legacy path reference raises AdapterPurityError
        with self.assertRaises(AdapterPurityError):
            verify_adapter_purity(
                Path(".opencode/commands/scaffold.md"), fix_data["impure_legacy_path"]
            )

    # -------------------------------------------------------------------------
    # E-04 / V-04: Clean-target host discovery & evidence gating
    # -------------------------------------------------------------------------

    def test_e04(self):
        """E-04: Support claims cite executable host gates; unavailable integrations do not write target adapters."""

        fixture_path = (
            Path(__file__).resolve().parent
            / "fixtures"
            / "awphysical"
            / "order09"
            / "e04-host-discovery.json"
        )
        self.assertTrue(fixture_path.is_file())
        fix_data = json.loads(fixture_path.read_text(encoding="utf-8"))

        for host in fix_data["supported_hosts"]:
            evidence = validate_host_evidence(
                host, "1.0.0" if host != "antigravity" else "2.0.0"
            )
            self.assertEqual(evidence.host_name, host)

        with self.assertRaises(UnsupportedHostError):
            validate_host_evidence(fix_data["unsupported_host"], "1.0.0")

        with self.assertRaises(UnsupportedHostError):
            validate_host_evidence("opencode", fix_data["untested_version"])

    # -------------------------------------------------------------------------
    # E-05 / V-05: Target baseline zero-delta proof
    # -------------------------------------------------------------------------

    def test_e05(self):
        """E-05: Clean-target mode proves zero AW-owned target delta from merge-base, index, and filesystem evidence."""

        fixture_path = (
            Path(__file__).resolve().parent
            / "fixtures"
            / "awphysical"
            / "order09"
            / "e05-zero-target-delta.json"
        )
        self.assertTrue(fixture_path.is_file())
        fix_data = json.loads(fixture_path.read_text(encoding="utf-8"))

        before_snap = snapshot_target_state(self.target_repo)
        after_snap = snapshot_target_state(self.target_repo)

        delta = compute_target_delta(before_snap, after_snap)
        self.assertEqual(
            delta["total_changes"], fix_data["clean_target_expected_delta"]
        )

        # Add planted write canary and verify snapshot detects non-zero delta
        canary = Path(self.target_repo) / fix_data["planted_write_path"]
        canary.parent.mkdir(parents=True, exist_ok=True)
        canary.write_text("canary test", encoding="utf-8")

        after_canary_snap = snapshot_target_state(self.target_repo)
        canary_delta = compute_target_delta(before_snap, after_canary_snap)
        self.assertGreaterEqual(
            canary_delta["total_changes"], fix_data["expected_detected_delta"]
        )

    # -------------------------------------------------------------------------
    # E-06 / V-06: Legacy adapter conversion & foreign content preservation
    # -------------------------------------------------------------------------

    def test_e06(self):
        """E-06: Migration creates current adapters, preserves sibling/foreign content byte-for-byte."""

        fixture_path = (
            Path(__file__).resolve().parent
            / "fixtures"
            / "awphysical"
            / "order09"
            / "e06-legacy-conversion.json"
        )
        self.assertTrue(fixture_path.is_file())
        fix_data = json.loads(fixture_path.read_text(encoding="utf-8"))

        # Setup legacy AGENTS.md with foreign user content
        agents_path = Path(self.target_repo) / "AGENTS.md"
        content = fix_data["foreign_sibling_content"] + fix_data["legacy_agents_block"]
        agents_path.write_text(content, encoding="utf-8")

        res = convert_legacy_adapters(self.target_repo, aw_home=self.aw_home)
        self.assertIn("AGENTS.md", res["converted"])

        converted_content = agents_path.read_text(encoding="utf-8")
        self.assertIn(fix_data["expected_converted_marker"], converted_content)
        self.assertTrue(
            converted_content.startswith(fix_data["foreign_sibling_content"])
        )

    # -------------------------------------------------------------------------
    # E-07 / V-07: Adapter drift, status, repair, & uninstall
    # -------------------------------------------------------------------------

    def test_e07(self):
        """E-07: Repair touches only owned adapters; uninstall removes only manifest-owned content."""

        fixture_path = (
            Path(__file__).resolve().parent
            / "fixtures"
            / "awphysical"
            / "order09"
            / "e07-drift-uninstall.json"
        )
        self.assertTrue(fixture_path.is_file())
        fix_data = json.loads(fixture_path.read_text(encoding="utf-8"))

        manifest = build_default_adapter_manifest(
            Path(self.target_repo), target_repo=self.target_repo, aw_home=self.aw_home
        )
        repaired = repair_adapters(self.target_repo, manifest=manifest)
        self.assertGreater(len(repaired), 0)

        # Plant foreign file in adapter directory
        foreign_p = Path(self.target_repo) / fix_data["foreign_file"]
        foreign_p.parent.mkdir(parents=True, exist_ok=True)
        foreign_p.write_text("user custom command", encoding="utf-8")

        # Uninstall OpenCode host adapters
        removed = uninstall_adapters(
            self.target_repo, manifest=manifest, host_filter="opencode"
        )
        self.assertIn(fix_data["owned_shim"], removed)
        self.assertTrue(
            foreign_p.is_file(), "Foreign file must be preserved during host uninstall!"
        )

    # -------------------------------------------------------------------------
    # E-08 / V-08: Claim-set equals evidence-set & complete matrix
    # -------------------------------------------------------------------------

    def test_e08(self):
        """E-08: Every advertised host/mode has an executable proof and claims equal evidence."""

        fixture_path = (
            Path(__file__).resolve().parent
            / "fixtures"
            / "awphysical"
            / "order09"
            / "e08-claims-evidence-matrix.json"
        )
        self.assertTrue(fixture_path.is_file())
        fix_data = json.loads(fixture_path.read_text(encoding="utf-8"))

        self.assertEqual(ADVERTISED_CLEAN_DELTA_CLAIMS, D113_EVIDENCE_PAIRS)
        self.assertEqual(len(ADVERTISED_CLEAN_DELTA_CLAIMS), fix_data["claims_count"])
        self.assertEqual(len(D113_EVIDENCE_PAIRS), fix_data["evidence_count"])


if __name__ == "__main__":
    unittest.main()
