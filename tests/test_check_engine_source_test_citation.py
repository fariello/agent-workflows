"""Behavioral tests for check.source-test-citation-dangling rule (IPD ml7b9e).

Tests exercise observable engine behavior and outcome drift records only.
No tests inspect AST, inspect module internals, or read source files.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from agent_workflows import artifact_core as _core
from agent_workflows import check_engine


def _create_test_repo(root: Path) -> Path:
    """Create minimal directory structure for check_engine fixture tests."""
    repo = Path(root)
    (repo / "agent_workflows").mkdir(parents=True, exist_ok=True)
    (repo / "tools").mkdir(parents=True, exist_ok=True)
    (repo / "tests").mkdir(parents=True, exist_ok=True)
    for p in (
        repo / ".aw" / "records" / "plans" / "pending",
        repo / ".aw" / "records" / "plans" / "executed",
        repo / ".aw" / "records" / "specs" / "approved",
    ):
        p.mkdir(parents=True, exist_ok=True)
    return repo


class CheckEngineSourceTestCitationTests(unittest.TestCase):
    """Behavioral tests for check_source_test_citations and its check_types integration."""

    def test_case_01_missing_test_citation_fires_with_info_severity(self) -> None:
        """Case 1: a comment citing a missing tests/test_gone.py fires once at info with location."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = _create_test_repo(Path(tmp))
            target_py = repo / "agent_workflows" / "mod.py"
            target_py.write_text("# Cites tests/test_gone.py here\n", encoding="utf-8")

            findings = check_engine.check_source_test_citations(repo)
            self.assertEqual(len(findings), 1)
            finding = findings[0]
            self.assertEqual(finding.rule, "check.source-test-citation-dangling")
            self.assertEqual(finding.severity, "info")
            self.assertEqual(finding.location, "agent_workflows/mod.py:1")
            self.assertIn("tests/test_gone.py", finding.observed)
            self.assertIn("repoint", finding.recovery)

    def test_case_02_existing_test_file_citation_is_silent(self) -> None:
        """Case 2: a citation of an existing tests/test_here.py is silent."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = _create_test_repo(Path(tmp))
            (repo / "tests" / "test_here.py").write_text(
                "# test file\n", encoding="utf-8"
            )
            (repo / "agent_workflows" / "mod.py").write_text(
                "# Live pointer to tests/test_here.py\n", encoding="utf-8"
            )

            findings = check_engine.check_source_test_citations(repo)
            self.assertEqual(findings, [])

    def test_case_03_retirement_statement_is_silent(self) -> None:
        """Case 3: a retirement statement ('tests/test_gone.py was deleted in 19313eed') is silent."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = _create_test_repo(Path(tmp))
            (repo / "agent_workflows" / "mod.py").write_text(
                "# tests/test_gone.py was deleted in `19313eed`\n", encoding="utf-8"
            )

            findings = check_engine.check_source_test_citations(repo)
            self.assertEqual(findings, [])

    def test_case_04_deleted_without_hash_or_hex_without_digit_still_fires(
        self,
    ) -> None:
        """Case 4: 'deleted' without hash or with non-digit hex still fires (discriminating negative)."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = _create_test_repo(Path(tmp))
            (repo / "agent_workflows" / "mod1.py").write_text(
                "# tests/test_gone1.py was deleted\n", encoding="utf-8"
            )
            (repo / "agent_workflows" / "mod2.py").write_text(
                "# tests/test_gone2.py was deleted in `defaced`\n", encoding="utf-8"
            )

            findings = check_engine.check_source_test_citations(repo)
            self.assertEqual(len(findings), 2)
            observed_citations = {f.observed for f in findings}
            self.assertTrue(
                any("tests/test_gone1.py" in obs for obs in observed_citations)
            )
            self.assertTrue(
                any("tests/test_gone2.py" in obs for obs in observed_citations)
            )

    def test_case_05_placeholder_citations_are_silent(self) -> None:
        """Case 5: placeholder citations such as tests/test_x.py are silent."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = _create_test_repo(Path(tmp))
            (repo / "agent_workflows" / "mod.py").write_text(
                "# Examples: tests/test_x.py, tests/test_foo.py, tests/test_extra.py, tests/test_secret.py\n",
                encoding="utf-8",
            )

            findings = check_engine.check_source_test_citations(repo)
            self.assertEqual(findings, [])

    def test_case_06_deduplication_within_file_and_multi_file_reporting(self) -> None:
        """Case 6: same missing path cited twice in one file reports once; in two files reports twice."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = _create_test_repo(Path(tmp))
            (repo / "agent_workflows" / "mod1.py").write_text(
                "# First mention tests/test_gone.py\n# Second mention tests/test_gone.py\n",
                encoding="utf-8",
            )
            findings1 = check_engine.check_source_test_citations(repo)
            self.assertEqual(len(findings1), 1)
            self.assertEqual(findings1[0].location, "agent_workflows/mod1.py:1")

            (repo / "tools" / "tool.py").write_text(
                "# Tool mention tests/test_gone.py\n", encoding="utf-8"
            )
            findings2 = check_engine.check_source_test_citations(repo)
            self.assertEqual(len(findings2), 2)
            locations = {f.location for f in findings2}
            self.assertEqual(
                locations, {"agent_workflows/mod1.py:1", "tools/tool.py:1"}
            )

    def test_case_06b_retirement_then_live_mention_reports_at_later_line(self) -> None:
        """Case 6b: first mention is retirement statement, later mention is live claim; reports at later line."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = _create_test_repo(Path(tmp))
            (repo / "agent_workflows" / "mixed.py").write_text(
                "# Line 1: tests/test_gone.py was deleted in `19313eed`\n"
                "# Line 2: middle prose\n"
                "# Line 3: live claim of tests/test_gone.py\n",
                encoding="utf-8",
            )

            findings = check_engine.check_source_test_citations(repo)
            self.assertEqual(len(findings), 1)
            self.assertEqual(findings[0].location, "agent_workflows/mixed.py:3")

    def test_case_07_test_fixture_files_are_silent(self) -> None:
        """Case 7: citations inside test_fixture.py or file ending with _test.py are silent."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = _create_test_repo(Path(tmp))
            (repo / "tools" / "test_fixture.py").write_text(
                "# Fixture literal tests/test_gone.py\n", encoding="utf-8"
            )
            (repo / "agent_workflows" / "helper_test.py").write_text(
                "# Another test literal tests/test_gone.py\n", encoding="utf-8"
            )

            findings = check_engine.check_source_test_citations(repo)
            self.assertEqual(findings, [])

    def test_case_08_pycache_and_gitignore_exclusions(self) -> None:
        """Case 8: citation in __pycache__ or .gitignore directory is silent."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = _create_test_repo(Path(tmp))
            pycache_dir = repo / "agent_workflows" / "__pycache__"
            pycache_dir.mkdir(parents=True, exist_ok=True)
            (pycache_dir / "cached.py").write_text(
                "# tests/test_gone.py\n", encoding="utf-8"
            )

            # __pycache__ is in default ignored dirs without git
            findings = check_engine.check_source_test_citations(repo)
            self.assertEqual(findings, [])

            # .gitignore test with git if git is available
            git_bin = shutil.which("git")
            if git_bin is not None:
                subprocess.run([git_bin, "init", "-q"], cwd=repo, check=True)
                (repo / ".gitignore").write_text("ignored_dir/\n", encoding="utf-8")
                ignored_dir = repo / "agent_workflows" / "ignored_dir"
                ignored_dir.mkdir(parents=True, exist_ok=True)
                (ignored_dir / "ignored.py").write_text(
                    "# tests/test_gone.py\n", encoding="utf-8"
                )
                findings_git = check_engine.check_source_test_citations(repo)
                self.assertEqual(findings_git, [])

    def test_case_09_and_09b_advisory_severity_and_drift_exit_code_contrastive_pair(
        self,
    ) -> None:
        """Case 9 & 9b: severity is info and drift_exit_code is 0, warning contrastive pair is 1."""
        spec = check_engine.rule_spec("check.source-test-citation-dangling")
        self.assertEqual(spec.severity, "info")

        with tempfile.TemporaryDirectory() as tmp:
            repo = _create_test_repo(Path(tmp))
            (repo / "agent_workflows" / "mod.py").write_text(
                "# tests/test_gone.py\n", encoding="utf-8"
            )
            findings = check_engine.check_source_test_citations(repo)
            self.assertEqual(len(findings), 1)

            # Case 9: info severity produces drift_exit_code 0
            self.assertEqual(_core.drift_exit_code(findings), 0)

            # Case 9b: contrastive pair with warning severity produces drift_exit_code 1
            warning_findings = [f._replace(severity="warning") for f in findings]
            self.assertEqual(_core.drift_exit_code(warning_findings), 1)

    def test_case_10_check_types_all_integration(self) -> None:
        """Case 10: check_types(repo, ['all']) result contains the case 1 finding."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = _create_test_repo(Path(tmp))
            (repo / "agent_workflows" / "mod.py").write_text(
                "# tests/test_gone.py\n", encoding="utf-8"
            )

            all_findings = check_engine.check_types(repo, ["all"])
            matching = [
                f
                for f in all_findings
                if f.rule == "check.source-test-citation-dangling"
            ]
            self.assertEqual(len(matching), 1)
            self.assertEqual(matching[0].location, "agent_workflows/mod.py:1")
            self.assertEqual(matching[0].severity, "info")


if __name__ == "__main__":
    unittest.main()
