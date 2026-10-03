"""Tests for check.test-citation-dangling rule in check_engine (IPD h65phz).

Verifies:
1. A spec whose normative body cites a nonexistent `tests/test_*.py` FIRES
   with rule 'check.test-citation-dangling' at severity 'error'.
2. A spec whose normative body cites an existing `tests/test_*.py` is SILENT.
3. A spec whose `## Workflow history` cites a nonexistent `tests/test_*.py` is SILENT
   (verifying the dated history note exemption).
4. End-to-end integration via check_types(repo, ['specs']).
5. Live repository verification: zero findings across all specs.

Conforms to GUIDING_PRINCIPLES P16:
Exercises code by calling functions over synthesized fixture trees and asserting on
observable finding objects; never reads or inspects check_engine.py source.
"""

from __future__ import annotations

import pathlib
import tempfile
import unittest

from agent_workflows import check_engine


class TestCheckEngineTestCitation(unittest.TestCase):
    """Tests for check.test-citation-dangling rule."""

    def _create_fixture_repo(self, tmp_path: pathlib.Path) -> pathlib.Path:
        """Create minimal directory structure for check_engine specs test."""
        (tmp_path / ".aw" / "records" / "specs" / "approved").mkdir(
            parents=True, exist_ok=True
        )
        (tmp_path / "tests").mkdir(parents=True, exist_ok=True)
        return tmp_path

    def _write_spec(
        self,
        repo: pathlib.Path,
        slug: str,
        body: str,
        history: str = "",
    ) -> pathlib.Path:
        spec_path = (
            repo
            / ".aw"
            / "records"
            / "specs"
            / "approved"
            / f"20261001-tst001-01-tst001-{slug}.spec.md"
        )
        content = (
            f"# Spec: {slug}\n\n" "- Id: tst001\n" "- Status: approved\n\n" f"{body}\n"
        )
        if history:
            content += f"\n## Workflow history\n{history}\n"
        spec_path.write_text(content, encoding="utf-8")
        return spec_path

    def test_body_citation_to_nonexistent_path_fires(self) -> None:
        """Case 1: A body citation to a nonexistent tests/test_*.py FIRES."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = self._create_fixture_repo(pathlib.Path(tmp))
            self._write_spec(
                repo,
                "missing-guard",
                "This behavior is guarded by `tests/test_missing_file.py`.",
            )

            drifts = check_engine.check_spec_test_citations(repo)
            self.assertEqual(len(drifts), 1)
            finding = drifts[0]
            self.assertEqual(finding.rule, "check.test-citation-dangling")
            self.assertEqual(finding.severity, "error")
            self.assertIn("tests/test_missing_file.py", finding.detail)

    def test_body_citation_to_real_path_is_silent(self) -> None:
        """Case 2: A body citation to an existing tests/test_*.py is SILENT."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = self._create_fixture_repo(pathlib.Path(tmp))
            real_test = repo / "tests" / "test_real_file.py"
            real_test.write_text("# test\n", encoding="utf-8")

            self._write_spec(
                repo,
                "real-guard",
                "This behavior is guarded by `tests/test_real_file.py`.",
            )

            drifts = check_engine.check_spec_test_citations(repo)
            self.assertEqual(len(drifts), 0)

    def test_history_citation_to_nonexistent_path_is_silent(self) -> None:
        """Case 3: A ## Workflow history citation to a nonexistent tests/test_*.py is SILENT."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = self._create_fixture_repo(pathlib.Path(tmp))
            self._write_spec(
                repo,
                "history-citation",
                body="Normative body mentions no test file.",
                history="- 2026-09-21 note: Verified tests/test_deleted_suite.py passes.",
            )

            drifts = check_engine.check_spec_test_citations(repo)
            self.assertEqual(
                len(drifts),
                0,
                "Citations inside ## Workflow history must be exempt from dangling check",
            )

    def test_check_types_specs_end_to_end_integration(self) -> None:
        """Case 4: check_types(repo, ['specs']) end-to-end integration surfaces the rule."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = self._create_fixture_repo(pathlib.Path(tmp))
            self._write_spec(
                repo,
                "e2e-missing",
                "Guarded by `tests/test_e2e_nonexistent.py`.",
            )

            drifts = check_engine.check_types(repo, ["specs"])
            matching = [d for d in drifts if d.rule == "check.test-citation-dangling"]
            self.assertEqual(len(matching), 1)
            self.assertEqual(matching[0].severity, "error")
            self.assertIn("tests/test_e2e_nonexistent.py", matching[0].detail)

    def test_live_repository_is_clean(self) -> None:
        """Case 5: Over the live repository, the rule reports ZERO findings across all specs."""
        repo_root = pathlib.Path(__file__).resolve().parent.parent
        drifts = check_engine.check_spec_test_citations(repo_root)
        self.assertEqual(
            drifts,
            [],
            f"Expected zero dangling test citations in live specs tree, found: {drifts}",
        )
