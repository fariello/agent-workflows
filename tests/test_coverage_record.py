"""Tests for agent_workflows/coverage_record.py (spec 25kzda 2.5e, IPD 8mabmu E-03, E-06)."""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from agent_workflows import coverage_record
from agent_workflows import ipd_lifecycle as LC
from agent_workflows import ipd_lint as L
from agent_workflows import ipd_schema as S
from agent_workflows import runner_shared as rs
from tests import support


def _init_git(root: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "t@e.com"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "T"], cwd=root, check=True)
    (root / ".gitignore").write_text(".aw/state/\n", encoding="utf-8")


def _commit_all(root: Path, message: str) -> None:
    subprocess.run(["git", "add", "-A"], cwd=root, check=True)
    subprocess.run(["git", "commit", "-q", "-m", message], cwd=root, check=True)


class TestCoverageRecordReadWrite(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        _init_git(self.root)
        plans_dir = self.root / ".aw" / "records" / "plans" / "pending"
        plans_dir.mkdir(parents=True, exist_ok=True)
        self.plan_path = plans_dir / "20261004-demo-01-abc123-demo.ipd.md"
        self.plan_text = support.ready_plan_text(plan_id="abc123")
        self.plan_path.write_text(self.plan_text, encoding="utf-8")
        _commit_all(self.root, "initial commit")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_read_absent(self) -> None:
        rec = coverage_record.read(self.plan_text)
        self.assertEqual(rec.verdict, "absent")
        self.assertEqual(rec.fingerprint, "")
        self.assertEqual(rec.date, "")
        self.assertEqual(rec.model, "")
        self.assertEqual(rec.quotes, ())
        self.assertFalse(coverage_record.is_current(self.plan_text))

    def test_write_and_read_fail(self) -> None:
        quotes = [
            "obligation one from the orchestrator",
            "obligation two from the orchestrator",
        ]
        written = coverage_record.write(
            self.plan_path,
            "fail",
            quotes=quotes,
            model="claude-sonnet-4-6",
            tool="aw oc run",
            commit=False,
        )
        self.assertTrue(written)

        updated_text = self.plan_path.read_text(encoding="utf-8")
        self.assertIn("- Coverage: fail", updated_text)
        self.assertIn("- Coverage-Fingerprint: ", updated_text)
        self.assertIn("- Coverage-Checked: ", updated_text)
        self.assertIn("## Coverage findings", updated_text)
        self.assertIn('- "obligation one from the orchestrator"', updated_text)
        self.assertIn('- "obligation two from the orchestrator"', updated_text)
        self.assertIn("coverage fail (aw oc run): fingerprint ", updated_text)
        self.assertIn("model claude-sonnet-4-6", updated_text)

        # Check section ordering: ## Coverage findings must precede ## Validation and cross-check
        cov_idx = updated_text.find("## Coverage findings")
        val_idx = updated_text.find("## Validation and cross-check")
        self.assertNotEqual(cov_idx, -1)
        self.assertNotEqual(val_idx, -1)
        self.assertLess(cov_idx, val_idx)

        # Read back
        rec = coverage_record.read(updated_text)
        self.assertEqual(rec.verdict, "fail")
        self.assertEqual(rec.quotes, tuple(quotes))
        self.assertEqual(rec.model, "claude-sonnet-4-6")
        self.assertTrue(rec.fingerprint)
        self.assertTrue(coverage_record.is_current(updated_text))

        # Must lint conforming
        lint_res = L.lint_file(self.plan_path, checkpoint="author")
        self.assertEqual(
            lint_res.disposition,
            S.DISPOSITION_CONFORMING,
            [d.message for d in lint_res.diagnostics],
        )

    def test_checklist_edit_makes_is_current_false(self) -> None:
        coverage_record.write(
            self.plan_path,
            "fail",
            quotes=["uncovered obligation"],
            model="test-model",
            tool="aw oc run",
            commit=False,
        )
        text_after_write = self.plan_path.read_text(encoding="utf-8")
        self.assertTrue(coverage_record.is_current(text_after_write))

        # Modifying a checklist item modifies probe_cache_digest
        edited_text = text_after_write.replace("- [ ] E-01 ", "- [ ] E-01 edited ", 1)
        self.assertFalse(coverage_record.is_current(edited_text))

    def test_write_pass_removes_findings_and_lints_conforming(self) -> None:
        # First write fail with findings
        coverage_record.write(
            self.plan_path,
            "fail",
            quotes=["first obligation"],
            model="model-a",
            tool="aw oc run",
            commit=False,
        )
        self.assertIn(
            "## Coverage findings", self.plan_path.read_text(encoding="utf-8")
        )

        # Then overwrite with pass
        coverage_record.write(
            self.plan_path,
            "pass",
            quotes=[],
            model="model-a",
            tool="aw oc run",
            commit=False,
        )
        pass_text = self.plan_path.read_text(encoding="utf-8")
        self.assertIn("- Coverage: pass", pass_text)
        self.assertNotIn("## Coverage findings", pass_text)

        rec = coverage_record.read(pass_text)
        self.assertEqual(rec.verdict, "pass")
        self.assertEqual(rec.quotes, ())
        self.assertTrue(coverage_record.is_current(pass_text))

        lint_res = L.lint_file(self.plan_path, checkpoint="author")
        self.assertEqual(
            lint_res.disposition,
            S.DISPOSITION_CONFORMING,
            [d.message for d in lint_res.diagnostics],
        )

    def test_host_default_model_token(self) -> None:
        coverage_record.write(
            self.plan_path,
            "pass",
            quotes=[],
            model="",
            tool="aw oc run",
            commit=False,
        )
        text = self.plan_path.read_text(encoding="utf-8")
        self.assertIn("model by host-default", text)
        rec = coverage_record.read(text)
        self.assertEqual(rec.model, "by host-default")

    def test_metadata_replacement_in_place(self) -> None:
        coverage_record.write(
            self.plan_path,
            "fail",
            quotes=["foo"],
            model="m1",
            tool="aw oc run",
            commit=False,
        )
        coverage_record.write(
            self.plan_path,
            "pass",
            quotes=[],
            model="m2",
            tool="aw agy run",
            commit=False,
        )
        text = self.plan_path.read_text(encoding="utf-8")
        self.assertEqual(text.count("- Coverage:"), 1)
        self.assertEqual(text.count("- Coverage-Fingerprint:"), 1)
        self.assertEqual(text.count("- Coverage-Checked:"), 1)
        # Check order: Status is before Coverage
        status_pos = text.find("- Status:")
        cov_pos = text.find("- Coverage:")
        self.assertNotEqual(status_pos, -1)
        self.assertNotEqual(cov_pos, -1)
        self.assertLess(status_pos, cov_pos)


class TestCoverageFingerprintInvariance(unittest.TestCase):
    def setUp(self) -> None:
        support.declare_execution_role(self)
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        _init_git(self.root)
        plans_dir = self.root / ".aw" / "records" / "plans" / "pending"
        plans_dir.mkdir(parents=True, exist_ok=True)
        self.plan_path = plans_dir / "20261004-demo-01-abc123-demo.ipd.md"
        self.plan_text = support.ready_plan_text(plan_id="abc123")
        self.plan_path.write_text(self.plan_text, encoding="utf-8")
        _commit_all(self.root, "initial commit")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_fingerprints_unchanged_and_receipt_stays_current(self) -> None:
        # Begin execution to write real begin receipt
        begin_result = LC.begin(
            self.root, self.plan_path, "opencode/test", timestamp="2026-10-06T12:00:00Z"
        )
        self.assertEqual(begin_result.exit_code, LC.EXIT_OK, begin_result.message)
        receipt = begin_result.receipt
        self.assertIsNotNone(receipt)

        orig_text = self.plan_path.read_text(encoding="utf-8")
        self.assertTrue(LC.receipt_is_current(receipt, orig_text))

        orig_probe_digest = rs.probe_cache_digest(orig_text)
        orig_frozen_digest = LC.frozen_region_digest(orig_text)

        # 1. Record fail coverage answer
        written = coverage_record.write(
            self.plan_path,
            "fail",
            quotes=["some uncovered obligation"],
            model="model-test",
            tool="aw oc run",
            commit=False,
        )
        self.assertTrue(written)

        text_fail = self.plan_path.read_text(encoding="utf-8")
        self.assertEqual(rs.probe_cache_digest(text_fail), orig_probe_digest)
        self.assertEqual(LC.frozen_region_digest(text_fail), orig_frozen_digest)
        self.assertTrue(LC.receipt_is_current(receipt, text_fail))

        # 2. Record pass coverage answer
        written_pass = coverage_record.write(
            self.plan_path,
            "pass",
            quotes=[],
            model="model-test",
            tool="aw oc run",
            commit=False,
        )
        self.assertTrue(written_pass)

        text_pass = self.plan_path.read_text(encoding="utf-8")
        self.assertEqual(rs.probe_cache_digest(text_pass), orig_probe_digest)
        self.assertEqual(LC.frozen_region_digest(text_pass), orig_frozen_digest)
        self.assertTrue(LC.receipt_is_current(receipt, text_pass))
