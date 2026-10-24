"""Direct behavioral test coverage for config review-findings gate readers.

Restores core-tier behavioral coverage for backlog item yvmxs9 (plan f6el0l),
covering the two review_findings_gate keys identified in findings wo21z5:
config.read_review_findings_gate and config.findings_gate_threshold.

The control file tests/test_plan_readiness_recheck.py exercised threshold
fallback but could not kill read_review_findings_gate because its fixture value
matched the fail-closed default. These tests call the readers directly against
isolated temporary project configs.
"""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
from typing import Any
import unittest

import pytest

from agent_workflows import config

pytestmark = pytest.mark.core


class TestConfigReviewFindingsGate(unittest.TestCase):
    """Behavioral tests for review_findings_gate config readers."""

    def _make_repo(self, payload: Any = None) -> Path:
        """Create an isolated repo with optional .aw/config/project.json."""
        td = tempfile.TemporaryDirectory(prefix="aw_test_config_gate_")
        self.addCleanup(td.cleanup)
        repo = Path(td.name)
        if payload is not None:
            cfg = repo / ".aw" / "config"
            cfg.mkdir(parents=True, exist_ok=True)
            p = cfg / "project.json"
            if isinstance(payload, str):
                p.write_text(payload, encoding="utf-8")
            else:
                p.write_text(json.dumps(payload), encoding="utf-8")
        return repo

    def test_read_review_findings_gate_object(self) -> None:
        """(a) Returns the object unchanged for dict payload."""
        repo = self._make_repo({"review_findings_gate": {"block_at": "medium"}})
        res = config.read_review_findings_gate(repo)
        self.assertEqual(res, {"block_at": "medium"})

    def test_read_review_findings_gate_bare_string(self) -> None:
        """(b) Normalizes a bare string '  off ' to {'block_at': 'off'}."""
        repo = self._make_repo({"review_findings_gate": "  off "})
        res = config.read_review_findings_gate(repo)
        self.assertEqual(res, {"block_at": "off"})

    def test_read_review_findings_gate_none_cases(self) -> None:
        """(c) Returns None for missing file, unparseable JSON, non-dict top level, and absent key."""
        cases = [
            ("missing file", None),
            ("unparseable JSON", "{not json"),
            ("non-object top level", [1, 2, 3]),
            ("absent key", {"other_key": "val"}),
        ]
        for label, content in cases:
            with self.subTest(case=label):
                repo = self._make_repo(content)
                res = config.read_review_findings_gate(repo)
                self.assertIsNone(
                    res,
                    f"Row {label!r}: expected None, got {res!r}",
                )

    def test_findings_gate_threshold_matrix(self) -> None:
        """(d) Returns expected threshold row by row, falling back to fail-closed 'high'."""
        rows = [
            (
                "block_at: medium",
                {"review_findings_gate": {"block_at": "medium"}},
                "medium",
            ),
            (
                '" BLOCKER "',
                {"review_findings_gate": {"block_at": " BLOCKER "}},
                "blocker",
            ),
            ("off", {"review_findings_gate": {"block_at": "off"}}, "off"),
            ("bare-string form", {"review_findings_gate": "medium"}, "medium"),
            ("absent file", None, "high"),
            ("absent key", {}, "high"),
            ("typo hgih", {"review_findings_gate": {"block_at": "hgih"}}, "high"),
            ("non-string value 3", {"review_findings_gate": {"block_at": 3}}, "high"),
        ]
        for label, payload, expected in rows:
            with self.subTest(row=label):
                repo = self._make_repo(payload)
                actual = config.findings_gate_threshold(repo)
                self.assertEqual(
                    actual,
                    expected,
                    f"Row {label!r} failed: expected {expected!r}, got {actual!r}",
                )
