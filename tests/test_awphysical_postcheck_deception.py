"""Tests for the 11 deceptive postcheck fixtures and clean-independent fixture (Order 10 E-07 & V-07)."""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from tools.awphysical import aw_layout_postcheck as POSTCHECK


class TestPostcheckDeception(unittest.TestCase):
    """Test every deceptive fixture fails its exact mapped rule and exit code, while clean passes."""

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.base_dir = Path(self.tmp_dir)
        self.target = self.base_dir / "target"
        self.target.mkdir()

        self.authority = self.base_dir / "authority.json"
        self.authority.write_text(
            '{"authoritative_layout":"physical-aw-v2"}\n', encoding="utf-8"
        )

        self.receipt = self.base_dir / "receipt.json"
        self.receipt.write_text(
            '{"phase":"verified","legacy_writer_enabled":false,"rollback_ready":true}\n',
            encoding="utf-8",
        )

        self.adapter = self.base_dir / "adapter.md"
        self.adapter.write_text(
            "Read .aw/system/workflows/example.md\n", encoding="utf-8"
        )
        self.manifest = self.base_dir / "adapters.json"
        self.manifest.write_text(
            json.dumps({"adapters": [str(self.adapter)]}), encoding="utf-8"
        )

        self.plan_out = self.target / ".aw/records/plans/plan.md"
        self.plan_out.parent.mkdir(parents=True, exist_ok=True)
        self.plan_out.write_text("plan\n", encoding="utf-8")

        self.valid_context = {
            "target_repo": str(self.target),
            "authority_file": str(self.authority),
            "transaction_receipt": str(self.receipt),
            "adapter_manifest": str(self.manifest),
            "roots": {
                "system": {
                    "path": str(self.target / ".aw/system"),
                    "git_policy": "tracked",
                },
                "config_project": {
                    "path": str(self.target / ".aw/config"),
                    "git_policy": "tracked",
                },
                "config_local": {
                    "path": str(self.base_dir / "config_local.json"),
                    "git_policy": "untracked",
                },
                "state_durable": {
                    "path": str(self.target / ".aw/state/durable"),
                    "git_policy": "tracked",
                },
                "state_runtime": {
                    "path": str(self.base_dir / "runtime"),
                    "git_policy": "untracked",
                },
                "records": {
                    "path": str(self.target / ".aw/records"),
                    "git_policy": "tracked",
                },
            },
            "producer_routes": [
                {
                    "producer": "plans",
                    "logical_destination": "records/plans",
                    "verified": True,
                    "observed_path": str(self.plan_out),
                }
            ],
        }

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_clean_independent(self):
        """Clean fixture must pass postcheck with valid status."""
        report = POSTCHECK.check_context(self.valid_context)
        self.assertTrue(
            report["valid"], f"Clean context failed: {report.get('findings')}"
        )

    def test_deceptive_fabricated_clean_context(self):
        """Fabricated clean context missing authority file must fail authority-evidence-missing."""
        ctx = dict(self.valid_context)
        ctx.pop("authority_file")
        report = POSTCHECK.check_context(ctx)
        self.assertFalse(report["valid"])
        rules = {f["rule"] for f in report["findings"]}
        self.assertIn("authority-evidence-missing", rules)

    def test_deceptive_missing_file(self):
        """Missing producer output path must fail producer-output-missing."""
        ctx = dict(self.valid_context)
        ctx["producer_routes"] = [
            {
                "producer": "plans",
                "logical_destination": "records/plans",
                "verified": True,
                "observed_path": str(self.base_dir / "nonexistent_file.md"),
            }
        ]
        report = POSTCHECK.check_context(ctx)
        self.assertFalse(report["valid"])
        rules = {f["rule"] for f in report["findings"]}
        self.assertIn("producer-output-missing", rules)

    def test_deceptive_stale_hash(self):
        """Stale hash evidence must fail stale-hash."""
        ctx = dict(self.valid_context)
        ctx["hash_evidence"] = [
            {"path": "sample.md", "expected_hash": "hash_a", "actual_hash": "hash_b"}
        ]
        report = POSTCHECK.check_context(ctx)
        self.assertFalse(report["valid"])
        rules = {f["rule"] for f in report["findings"]}
        self.assertIn("stale-hash", rules)

    def test_deceptive_wrong_destination(self):
        """Producer writing outside records/state roots must fail producer-output-wrong-root."""
        wrong_file = self.base_dir / "wrong_location.md"
        wrong_file.write_text("wrong", encoding="utf-8")
        ctx = dict(self.valid_context)
        ctx["producer_routes"] = [
            {
                "producer": "plans",
                "logical_destination": "records/plans",
                "verified": True,
                "observed_path": str(wrong_file),
            }
        ]
        report = POSTCHECK.check_context(ctx)
        self.assertFalse(report["valid"])
        rules = {f["rule"] for f in report["findings"]}
        self.assertIn("producer-output-wrong-root", rules)

    def test_deceptive_wrong_git_index(self):
        """Mismatched git owner must fail wrong-git-index."""
        ctx = dict(self.valid_context)
        ctx["producer_routes"] = [
            {
                "producer": "plans",
                "logical_destination": "records/plans",
                "verified": True,
                "observed_path": str(self.plan_out),
                "git_owner": str(self.base_dir / "wrong_git_owner"),
            }
        ]
        report = POSTCHECK.check_context(ctx)
        self.assertFalse(report["valid"])
        rules = {f["rule"] for f in report["findings"]}
        self.assertIn("wrong-git-index", rules)

    def test_deceptive_ignored_leakage(self):
        """Runtime state tracked must fail prohibited-tracking-policy."""
        ctx = dict(self.valid_context)
        ctx_roots = dict(ctx["roots"])
        ctx_roots["state_runtime"] = {
            "path": str(self.target / ".aw/state/runtime"),
            "git_policy": "tracked",
        }
        ctx["roots"] = ctx_roots
        report = POSTCHECK.check_context(ctx)
        self.assertFalse(report["valid"])
        rules = {f["rule"] for f in report["findings"]}
        self.assertIn("prohibited-tracking-policy", rules)

    def test_deceptive_legacy_write(self):
        """Legacy write destination must fail producer-legacy-write."""
        ctx = dict(self.valid_context)
        ctx["producer_routes"] = [
            {
                "producer": "plans",
                "logical_destination": ".agents/plans",
                "verified": True,
                "observed_path": str(self.plan_out),
            }
        ]
        report = POSTCHECK.check_context(ctx)
        self.assertFalse(report["valid"])
        rules = {f["rule"] for f in report["findings"]}
        self.assertIn("producer-legacy-write", rules)

    def test_deceptive_copied_adapter_logic(self):
        """Adapter copying normative logic must fail adapter-copied-logic."""
        bad_adapter = self.base_dir / "bad_adapter.md"
        bad_adapter.write_text("# Workflow:\n" + "copied step\n" * 90, encoding="utf-8")
        manifest = self.base_dir / "bad_manifest.json"
        manifest.write_text(
            json.dumps({"adapters": [str(bad_adapter)]}), encoding="utf-8"
        )
        ctx = dict(self.valid_context)
        ctx["adapter_manifest"] = str(manifest)
        report = POSTCHECK.check_context(ctx)
        self.assertFalse(report["valid"])
        rules = {f["rule"] for f in report["findings"]}
        self.assertIn("adapter-copied-logic", rules)

    def test_deceptive_inaccessible_external_root(self):
        """Inaccessible external root path must fail inaccessible-external-root."""
        ctx = dict(self.valid_context)
        ctx_roots = dict(ctx["roots"])
        ctx_roots["config_local"] = {
            "path": str(self.base_dir / "nonexistent_dir" / "config_local.json"),
            "git_policy": "untracked",
        }
        ctx["roots"] = ctx_roots
        report = POSTCHECK.check_context(ctx)
        self.assertFalse(report["valid"])
        rules = {f["rule"] for f in report["findings"]}
        self.assertIn("inaccessible-external-root", rules)

    def test_deceptive_broken_rollback(self):
        """Rollback not ready in receipt must fail rollback-not-ready."""
        receipt = self.base_dir / "broken_receipt.json"
        receipt.write_text(
            '{"phase":"verified","legacy_writer_enabled":false,"rollback_ready":false}\n',
            encoding="utf-8",
        )
        ctx = dict(self.valid_context)
        ctx["transaction_receipt"] = str(receipt)
        report = POSTCHECK.check_context(ctx)
        self.assertFalse(report["valid"])
        rules = {f["rule"] for f in report["findings"]}
        self.assertIn("rollback-not-ready", rules)

    def test_deceptive_skipped_companion_check(self):
        """Skipped companion check when companion exists must fail skipped-companion-check."""
        ctx = dict(self.valid_context)
        ctx["has_companion"] = True
        ctx["companion_checked"] = False
        report = POSTCHECK.check_context(ctx)
        self.assertFalse(report["valid"])
        rules = {f["rule"] for f in report["findings"]}
        self.assertIn("skipped-companion-check", rules)


if __name__ == "__main__":
    unittest.main()
