"""Unit tests for clean-delta skills, D113 host evidence, and zero-target-write guarantees (IPD 20260809-awlayout-10)."""

from __future__ import annotations

import os
import shutil
import tempfile
import unittest
from pathlib import Path

from agent_workflows.clean_delta import (
    ADVERTISED_CLEAN_DELTA_CLAIMS,
    D113_EVIDENCE_PAIRS,
    CleanDeltaManager,
    UnsupportedHostError,
    validate_host_evidence,
)
from agent_workflows.project_registry import register_or_update_project


class TestCleanDeltaSkillsAndHostGates(unittest.TestCase):
    """Test D113 evidence gating, claim-set equality, and zero-target-write invariants."""

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.target_repo = os.path.join(self.tmp_dir, "myrepo")
        os.makedirs(os.path.join(self.target_repo, ".git"), exist_ok=True)
        self.aw_home = os.path.join(self.tmp_dir, "aw_home")
        os.makedirs(self.aw_home, exist_ok=True)
        self.user_skills_dir = os.path.join(self.tmp_dir, "user_skills")
        os.makedirs(self.user_skills_dir, exist_ok=True)

        os.environ["AW_HOME"] = self.aw_home
        register_or_update_project(
            self.target_repo, self.aw_home, project_id="myrepo-123456"
        )

    def tearDown(self):
        os.environ.pop("AW_HOME", None)
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_claim_set_equality_assertion(self):
        """Advertised clean-delta claims MUST exactly equal D113 evidence pairs (E-01 & L10-01 & V-05)."""
        self.assertEqual(
            ADVERTISED_CLEAN_DELTA_CLAIMS,
            D113_EVIDENCE_PAIRS,
            "Advertised clean-delta host/version claims do not equal D113 evidence pairs!",
        )

    def test_unproven_host_version_refusal(self):
        """Clean-delta MUST be refused for host or version lacking D113 evidence (E-01 & V-02)."""
        with self.assertRaises(UnsupportedHostError):
            validate_host_evidence("unsupported_host", "1.0.0")

        with self.assertRaises(UnsupportedHostError):
            validate_host_evidence("opencode", "99.0.0")  # Untested host version

    def test_proven_host_validation_success(self):
        """Proven host and version validate successfully (E-01)."""
        evidence = validate_host_evidence("opencode", "1.0.0")
        self.assertEqual(evidence.host_name, "opencode")
        self.assertEqual(evidence.version, "1.0.0")

    def test_clean_delta_zero_target_write_invariant(self):
        """Clean-delta install MUST leave target repository work-tree with zero AW files (E-04 & V-04)."""
        mgr = CleanDeltaManager(target_repo=self.target_repo, aw_home=self.aw_home)
        res = mgr.install_clean_delta(
            "opencode", "1.0.0", user_skills_dir=self.user_skills_dir
        )

        self.assertEqual(res["status"], "installed")
        self.assertEqual(res["target_writes"], 0)

        # INVARIANT: Target repo MUST NOT contain `.aw/` directory in clean-delta mode!
        target_aw = Path(self.target_repo) / ".aw"
        self.assertFalse(
            target_aw.exists(),
            "Target repository contained .aw/ directory after clean-delta install!",
        )


if __name__ == "__main__":
    unittest.main()
