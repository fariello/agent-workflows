"""Tests for aw check severity tally in rules evidence row (IPD tzjtg4).

Verifies that aw check tallies findings by their enriched/registered severity
(errors, warnings, info) rather than rule-name prefixes, resolving the
contradiction where an advisory is reported as an error.
"""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from tests.support import init_repo, run_cli


class CheckSeverityTallyTests(unittest.TestCase):
    """Behavior tests pinning the aw check severity-based tally."""

    def _setup_mixed_severity_repo(self, root: Path) -> Path:
        """Create a fixture repo that provokes error, warning, and info findings."""
        repo = init_repo(root)

        # 1. Warning finding: setid length > 14 with --strict-setid-length
        specs_dir = repo / ".aw" / "records" / "specs"
        specs_dir.mkdir(parents=True, exist_ok=True)
        fn_spec = "20261001-abcdefghijklmno-01-a1b2c3-test.spec.md"
        (specs_dir / fn_spec).write_text(
            "# Spec: Test\n\n"
            "- Date: 2026-10-01\n"
            "- Status: draft\n"
            "- Id: a1b2c3\n\n"
            "## Workflow history\n"
            "- 2026-10-01 draft: created\n",
            encoding="utf-8",
        )

        # 2. Info finding: draft plan in pending
        plans_dir = repo / ".aw" / "records" / "plans" / "pending"
        plans_dir.mkdir(parents=True, exist_ok=True)
        fn_plan = "20261001-testset-01-p1p2p3-test.ipd.md"
        (plans_dir / fn_plan).write_text(
            "# IPD: Test Plan\n\n"
            "- Date: 2026-10-01\n"
            "- Status: draft\n"
            "- Set: testset\n"
            "- Id: p1p2p3\n",
            encoding="utf-8",
        )

        # 3. Error findings: non-conforming file in backlog
        backlog_dir = repo / ".aw" / "records" / "backlog" / "open"
        backlog_dir.mkdir(parents=True, exist_ok=True)
        (backlog_dir / "bad-name.md").write_text("bad", encoding="utf-8")

        return repo

    def test_three_way_severity_split(self):
        """Property 1: The rules evidence row reports errors, warnings, and info distinctly."""
        with tempfile.TemporaryDirectory() as td:
            repo = self._setup_mixed_severity_repo(Path(td))
            res = run_cli("check", "all", "--strict-setid-length", "--json", cwd=repo)
            self.assertEqual(res.returncode, 1)
            data = json.loads(res.stdout)

            findings = data["data"]["policy_findings"]
            exp_errors = sum(1 for f in findings if f["severity"] == "error")
            exp_warnings = sum(1 for f in findings if f["severity"] == "warning")
            exp_info = sum(1 for f in findings if f["severity"] == "info")

            self.assertGreater(exp_errors, 0, "fixture must contain errors")
            self.assertGreater(exp_warnings, 0, "fixture must contain warnings")
            self.assertGreater(exp_info, 0, "fixture must contain info findings")

            rules_evidence = next(
                (e for e in data["evidence"] if e["key"] == "rules"), None
            )
            self.assertIsNotNone(rules_evidence, "rules evidence row must exist")
            val = rules_evidence["value"]

            self.assertEqual(val.get("errors"), exp_errors)
            self.assertEqual(val.get("warnings"), exp_warnings)
            self.assertEqual(val.get("info"), exp_info)

    def test_clean_run_contradiction_resolved(self):
        """Property 2: An info-only run exits 0 and does not report nonzero errors beside CONFORMS."""
        with tempfile.TemporaryDirectory() as td:
            repo = init_repo(Path(td))
            (repo / ".aw" / "records" / "specs").mkdir(parents=True, exist_ok=True)

            # Human-readable check: CONFORMS must be paired with errors 0, not errors 1
            human_res = run_cli("check", "specs", "--no-color", cwd=repo)
            self.assertEqual(human_res.returncode, 0)
            self.assertIn("CONFORMS", human_res.stdout)
            self.assertIn("errors  0", human_res.stdout)
            self.assertNotIn("errors  1", human_res.stdout)

            # Structured check
            json_res = run_cli("check", "specs", "--json", cwd=repo)
            self.assertEqual(json_res.returncode, 0)
            data = json.loads(json_res.stdout)
            self.assertEqual(data["status"], "conforms")
            self.assertEqual(data["exit_code"], 0)

            rules_evidence = next(
                (e for e in data["evidence"] if e["key"] == "rules"), None
            )
            self.assertIsNotNone(rules_evidence)
            val = rules_evidence["value"]
            self.assertEqual(val.get("errors"), 0)
            self.assertEqual(val.get("warnings"), 0)
            self.assertEqual(val.get("info"), 1)

    def test_count_conservation_invariant(self):
        """Property 3: Sum of errors, warnings, and info equals total findings."""
        with tempfile.TemporaryDirectory() as td:
            repo = self._setup_mixed_severity_repo(Path(td))
            res = run_cli("check", "all", "--strict-setid-length", "--json", cwd=repo)
            data = json.loads(res.stdout)

            findings = data["data"]["policy_findings"]
            total_findings = len(findings)

            rules_evidence = next(
                (e for e in data["evidence"] if e["key"] == "rules"), None
            )
            self.assertIsNotNone(rules_evidence)
            val = rules_evidence["value"]

            self.assertIn("errors", val)
            self.assertIn("warnings", val)
            self.assertIn("info", val)
            tally_sum = val["errors"] + val["warnings"] + val["info"]
            self.assertEqual(tally_sum, total_findings)

    def test_exit_code_independence(self):
        """Property 4: Severity tally changes do not affect drift_exit_code semantics."""
        with tempfile.TemporaryDirectory() as td:
            # Info-only run exits 0
            repo_info = init_repo(Path(td) / "info_repo")
            (repo_info / ".aw" / "records" / "specs").mkdir(parents=True, exist_ok=True)
            res_info = run_cli("check", "specs", "--json", cwd=repo_info)
            self.assertEqual(res_info.returncode, 0)
            data_info = json.loads(res_info.stdout)
            self.assertEqual(data_info["exit_code"], 0)
            self.assertEqual(data_info["status"], "conforms")

            # Mixed-severity run with errors/warnings exits 1
            repo_mixed = self._setup_mixed_severity_repo(Path(td) / "mixed_repo")
            res_mixed = run_cli(
                "check", "all", "--strict-setid-length", "--json", cwd=repo_mixed
            )
            self.assertEqual(res_mixed.returncode, 1)
            data_mixed = json.loads(res_mixed.stdout)
            self.assertEqual(data_mixed["exit_code"], 1)
            self.assertEqual(data_mixed["status"], "findings")


if __name__ == "__main__":
    unittest.main()
