"""Behavioral tests for status-agnostic glob Scope-Paths entries.

Plan yrq57q / backlog ho7qjb.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_workflows import check_engine, ipd_lifecycle, ipd_schema
from tests import support
from tests.test_oc_runipd import _CONFORMING_PLAN


class ScopePathsStatusAgnosticTests(unittest.TestCase):
    def setUp(self) -> None:
        support.declare_execution_role(self)

    def test_01_glob_form_is_legal_entry(self) -> None:
        """(a) Glob entry is legal in Scope-Paths and parsed intact."""
        backlog_pattern = (
            ".aw/records/backlog/**/20261002-scoperewrite-01-ho7qjb-x.backlog.md"
        )
        self.assertIsNone(ipd_schema._scope_path_entry_error(backlog_pattern))
        paths, is_grandfathered, errors = ipd_schema.parse_scope_paths(backlog_pattern)
        self.assertEqual(paths, [backlog_pattern])
        self.assertFalse(is_grandfathered)
        self.assertEqual(errors, [])

        spec_pattern = (
            ".aw/records/specs/**/20260802-1904-01-ipd-structure-and-linting.spec.md"
        )
        self.assertIsNone(ipd_schema._scope_path_entry_error(spec_pattern))
        paths_sp, grandfathered_sp, errors_sp = ipd_schema.parse_scope_paths(
            spec_pattern
        )
        self.assertEqual(paths_sp, [spec_pattern])
        self.assertFalse(grandfathered_sp)
        self.assertEqual(errors_sp, [])

    def test_02_scope_match_exact_basename_across_statuses(self) -> None:
        """(b) _scope_match matches exact basename across status dirs, rejects others."""
        backlog_dirs = ("open", "graduated", "blocked", "parked", "done")
        backlog_pattern = (
            ".aw/records/backlog/**/20261002-scoperewrite-01-ho7qjb-x.backlog.md"
        )
        for d in backlog_dirs:
            exact = (
                f".aw/records/backlog/{d}/20261002-scoperewrite-01-ho7qjb-x.backlog.md"
            )
            self.assertTrue(ipd_lifecycle._scope_match(exact, backlog_pattern))
            diff_name = (
                f".aw/records/backlog/{d}/20261002-scoperewrite-01-other-y.backlog.md"
            )
            self.assertFalse(ipd_lifecycle._scope_match(diff_name, backlog_pattern))
            self.assertFalse(
                ipd_lifecycle._scope_match(f"{exact}.bak", backlog_pattern)
            )
            self.assertFalse(ipd_lifecycle._scope_match(f"{exact}x", backlog_pattern))

        spec_dirs = (
            "draft",
            "to-review",
            "reviewed",
            "approved",
            "implementing",
            "implemented",
            "deferred",
            "superseded",
            "parked",
        )
        spec_pattern = (
            ".aw/records/specs/**/20260802-1904-01-ipd-structure-and-linting.spec.md"
        )
        for d in spec_dirs:
            exact = f".aw/records/specs/{d}/20260802-1904-01-ipd-structure-and-linting.spec.md"
            self.assertTrue(ipd_lifecycle._scope_match(exact, spec_pattern))
            diff_name = f".aw/records/specs/{d}/different.spec.md"
            self.assertFalse(ipd_lifecycle._scope_match(diff_name, spec_pattern))
            self.assertFalse(ipd_lifecycle._scope_match(f"{exact}.bak", spec_pattern))
            self.assertFalse(ipd_lifecycle._scope_match(f"{exact}x", spec_pattern))

    def test_03_stale_record_scope_paths_reports_moved_literal_and_clean_glob(
        self,
    ) -> None:
        """(c) stale_record_scope_paths reports literal form moved and glob form clean."""
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            graduated_dir = repo / ".aw" / "records" / "backlog" / "graduated"
            graduated_dir.mkdir(parents=True)
            target = graduated_dir / "20261002-scoperewrite-01-ho7qjb-x.backlog.md"
            target.write_text(
                "# Backlog: Target\n- Status: graduated\n- Id: ho7qjb\n",
                encoding="utf-8",
            )

            lit_path = (
                ".aw/records/backlog/open/20261002-scoperewrite-01-ho7qjb-x.backlog.md"
            )
            lit_plan = f"# IPD: Subj\n- Status: approved\n- Scope-Paths: {lit_path}\n"
            res_lit = check_engine.stale_record_scope_paths(repo, lit_plan)
            self.assertEqual(len(res_lit), 1)
            self.assertEqual(res_lit[0].path, lit_path)
            self.assertEqual(res_lit[0].classification, check_engine.SCOPE_STALE_MOVED)
            self.assertEqual(
                res_lit[0].resolved,
                (target.relative_to(repo).as_posix(),),
            )

            glob_path = (
                ".aw/records/backlog/**/20261002-scoperewrite-01-ho7qjb-x.backlog.md"
            )
            glob_plan = f"# IPD: Subj\n- Status: approved\n- Scope-Paths: {glob_path}\n"
            res_glob = check_engine.stale_record_scope_paths(repo, glob_plan)
            self.assertEqual(res_glob, [])

    def test_04_stale_record_scope_paths_blind_spot_on_unmatched_glob(self) -> None:
        """(d) Known blind spot (Finding F-03): stale_record_scope_paths skips glob entries."""
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            # A glob that matches no file on disk returns [] because the stale-path
            # check only evaluates literal file paths.
            nonexistent_glob = (
                ".aw/records/backlog/**/20261002-nonexistent-01-notfound.backlog.md"
            )
            glob_plan = (
                f"# IPD: Subj\n- Status: approved\n- Scope-Paths: {nonexistent_glob}\n"
            )
            res_glob = check_engine.stale_record_scope_paths(repo, glob_plan)
            self.assertEqual(res_glob, [])

            # By contrast, the literal form of a nonexistent file is reported as vanished.
            nonexistent_lit = (
                ".aw/records/backlog/open/20261002-nonexistent-01-notfound.backlog.md"
            )
            lit_plan = (
                f"# IPD: Subj\n- Status: approved\n- Scope-Paths: {nonexistent_lit}\n"
            )
            res_lit = check_engine.stale_record_scope_paths(repo, lit_plan)
            self.assertEqual(len(res_lit), 1)
            self.assertEqual(res_lit[0].path, nonexistent_lit)
            self.assertEqual(
                res_lit[0].classification, check_engine.SCOPE_STALE_VANISHED
            )

    def test_05_widening_asymmetry_from_frozen_receipt(self) -> None:
        """(e) Widening asymmetry (Finding F-02): receipt with glob accepts added literal, refuses added glob."""
        glob_path = (
            ".aw/records/backlog/**/20261002-scoperewrite-01-ho7qjb-x.backlog.md"
        )
        base_text = _CONFORMING_PLAN.replace(
            "Scope-Paths: src/", f"Scope-Paths: a.py, {glob_path}"
        )
        receipt = {
            "frozen_region_digest": ipd_lifecycle.frozen_region_digest(base_text),
            "scope_paths": ipd_lifecycle._frozen_scope_paths(base_text),
        }

        # Adding a literal entry is acceptable widening
        added_lit_text = _CONFORMING_PLAN.replace(
            "Scope-Paths: src/", f"Scope-Paths: a.py, {glob_path}, b.py"
        )
        cmp_lit = ipd_lifecycle.frozen_region_comparison(receipt, added_lit_text)
        self.assertTrue(cmp_lit.eligible)
        self.assertTrue(ipd_lifecycle.widening_is_acceptable(cmp_lit))

        # Adding a glob entry is refused widening
        added_glob_text = _CONFORMING_PLAN.replace(
            "Scope-Paths: src/",
            f"Scope-Paths: a.py, {glob_path}, .aw/records/specs/**/other.spec.md",
        )
        cmp_glob = ipd_lifecycle.frozen_region_comparison(receipt, added_glob_text)
        self.assertFalse(cmp_glob.eligible)
        self.assertFalse(ipd_lifecycle.widening_is_acceptable(cmp_glob))
        self.assertIn("DIRECTORY or GLOB", cmp_glob.ineligible_reason)

    def test_06_predicate_moved_terminal_backlog_vs_glob(self) -> None:
        """(f) Terminal backlog move (Finding F-06): literal is moved-terminal, glob is clean."""
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            done_dir = repo / ".aw" / "records" / "backlog" / "done"
            done_dir.mkdir(parents=True)
            target = done_dir / "20261002-scoperewrite-01-ho7qjb-x.backlog.md"
            target.write_text(
                "# Backlog: Target\n- Status: done\n- Id: ho7qjb\n",
                encoding="utf-8",
            )

            lit_path = (
                ".aw/records/backlog/open/20261002-scoperewrite-01-ho7qjb-x.backlog.md"
            )
            lit_plan = f"# IPD: Subj\n- Status: approved\n- Scope-Paths: {lit_path}\n"
            res_lit = check_engine.stale_record_scope_paths(repo, lit_plan)
            self.assertEqual(len(res_lit), 1)
            self.assertEqual(res_lit[0].path, lit_path)
            self.assertEqual(
                res_lit[0].classification, check_engine.SCOPE_STALE_MOVED_TERMINAL
            )
            self.assertEqual(
                res_lit[0].resolved,
                (target.relative_to(repo).as_posix(),),
            )

            glob_path = (
                ".aw/records/backlog/**/20261002-scoperewrite-01-ho7qjb-x.backlog.md"
            )
            glob_plan = f"# IPD: Subj\n- Status: approved\n- Scope-Paths: {glob_path}\n"
            res_glob = check_engine.stale_record_scope_paths(repo, glob_plan)
            self.assertEqual(res_glob, [])


if __name__ == "__main__":
    unittest.main()
