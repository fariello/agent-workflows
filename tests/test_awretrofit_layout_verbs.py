"""Regression tests for IPD awretrofit Order 01: record verbs must resolve the migrated `.aw/`
layout, not only the legacy `.agents/` tree.

Release-review run 20260817-153418 (finding S2-B01) found that the writer/board/lint record verbs
were left hardcoded to legacy `.agents/` after the awphysical migration, so on a migrated
(repository-backend `.aw/`) repo they silently no-op, false-pass a gate, or emit misleading errors.
The prior test suite masked this because every fixture built only `.agents/*` trees (S3-T01).

These tests build a repository-backend `.aw/records/*` fixture (no `.agents/`) and assert the fixed
verbs resolve it, plus a legacy-only case (fallback still works) and a mutation probe proving the
resolver is load-bearing.
"""

from __future__ import annotations

import argparse
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from agent_workflows import plans as plans_mod
from agent_workflows import ipd_lint
from agent_workflows.project_registry import register_or_update_project
from agent_workflows.project_schema import DeliveryMode, RecordsBackend
from agent_workflows.term import Term


def _write_plan(path: Path, status: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"# IPD: x\n\n- Status: {status}\n\n## Goal\n\nx\n", encoding="utf-8"
    )


class _RepositoryBackendFixture(unittest.TestCase):
    """Base: a repository-backend AW project whose records live under `.aw/records/` (no `.agents/`)."""

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.repo = Path(self.tmp_dir) / "repo"
        (self.repo / ".git").mkdir(parents=True)
        self.aw_home = Path(self.tmp_dir) / "aw_home"
        self.aw_home.mkdir(parents=True)
        self._prev_aw_home = os.environ.get("AW_HOME")
        os.environ["AW_HOME"] = str(self.aw_home)
        register_or_update_project(
            str(self.repo), str(self.aw_home), project_id="awretrofit-test"
        )
        config_dir = self.repo / ".aw" / "config"
        config_dir.mkdir(parents=True, exist_ok=True)
        (config_dir / "config.json").write_text(
            json.dumps(
                {
                    "delivery_mode": DeliveryMode.TRACKED.value,
                    "records_backend": RecordsBackend.REPOSITORY.value,
                    "aw_home": str(self.aw_home),
                }
            ),
            encoding="utf-8",
        )
        self.plans = self.repo / ".aw" / "records" / "plans"
        _write_plan(self.plans / "executed" / "20260101-0001-01-a.md", "executed")
        _write_plan(self.plans / "pending" / "20260101-0002-01-b.md", "approved")

    def tearDown(self):
        if self._prev_aw_home is None:
            os.environ.pop("AW_HOME", None)
        else:
            os.environ["AW_HOME"] = self._prev_aw_home
        import shutil

        shutil.rmtree(self.tmp_dir, ignore_errors=True)


class PlansBoardLayoutTests(_RepositoryBackendFixture):
    def test_scan_reads_aw_records_layout(self):
        """E-01/V-01: plans.scan resolves .aw/records/plans (no .agents/ present)."""
        recs = plans_mod.scan(self.repo)
        names = sorted(r.path.name for r in recs)
        self.assertEqual(names, ["20260101-0001-01-a.md", "20260101-0002-01-b.md"])
        # And every record path is under the migrated tree, not legacy.
        self.assertTrue(all(".aw/records/plans" in str(r.path) for r in recs))

    def test_board_does_not_short_circuit_on_missing_agents(self):
        """E-02/V-02: `aw plans` board lists the migrated plans instead of 'No plans found'."""
        from agent_workflows import cli

        args = argparse.Namespace(
            dir=str(self.repo), status_filter=None, pending=False, write_index=False
        )
        buf = io.StringIO()
        term = Term(stream=buf, color=False)
        rc = cli._run_plans(args, term)
        out = buf.getvalue()
        self.assertEqual(rc, 0)
        self.assertNotIn("No plans found", out)
        self.assertIn("20260101-0001-01-a.md", out)

    def test_write_index_targets_resolved_dir(self):
        """E-02/V-02: --write-index writes STATUS.md into the resolved .aw/records/plans dir."""
        from agent_workflows import cli

        args = argparse.Namespace(
            dir=str(self.repo), status_filter=None, pending=False, write_index=True
        )
        buf = io.StringIO()
        term = Term(stream=buf, color=False)
        rc = cli._run_plans(args, term)
        self.assertEqual(rc, 0)
        status = self.plans / "STATUS.md"
        self.assertTrue(status.is_file(), "STATUS.md not written to .aw/records/plans")
        self.assertFalse(
            (self.repo / ".agents" / "plans" / "STATUS.md").exists(),
            "STATUS.md leaked to the legacy .agents path",
        )

    def test_ipd_lint_all_finds_migrated_plans(self):
        """E-05/V-05: ipd_lint._iter_plan_files resolves .aw/records/plans (no false conforming=0)."""
        found = ipd_lint._iter_plan_files(self.repo)
        names = sorted(p.name for p in found)
        self.assertIn("20260101-0001-01-a.md", names)
        self.assertIn("20260101-0002-01-b.md", names)


class LegacyFallbackTests(unittest.TestCase):
    """The legacy `.agents/plans` read-fallback still works on a not-yet-migrated repo."""

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.repo = Path(self.tmp_dir)
        _write_plan(
            self.repo / ".agents" / "plans" / "pending" / "20260101-0001-01-y.md",
            "draft",
        )

    def tearDown(self):
        import shutil

        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_scan_falls_back_to_legacy(self):
        recs = plans_mod.scan(self.repo)
        self.assertEqual([r.path.name for r in recs], ["20260101-0001-01-y.md"])

    def test_ipd_lint_all_falls_back_to_legacy(self):
        found = ipd_lint._iter_plan_files(self.repo)
        self.assertEqual([p.name for p in found], ["20260101-0001-01-y.md"])


class ResearchAndRefsLayoutTests(_RepositoryBackendFixture):
    def test_research_root_resolves_migrated_layout(self):
        """E-04/V-04: the shared research-root resolver targets .aw/records/docs/research."""
        from agent_workflows import research_contract as R

        (self.repo / ".aw" / "records" / "docs" / "research").mkdir(
            parents=True, exist_ok=True
        )
        root = R.resolve_research_root(self.repo)
        self.assertTrue(str(root).startswith(str(self.repo)))
        self.assertIn(".aw/records/docs/research", str(root).replace("\\", "/"))

    def test_plans_refs_and_archive_resolve_migrated_layout(self):
        """E-03/V-03: plans_refs._dirs and plans_archive._dirs resolve .aw/records/plans."""
        from agent_workflows import plans_refs, plans_archive

        args = argparse.Namespace(dir=str(self.repo))
        _, refs_dir = plans_refs._dirs(args)
        _, arch_dir = plans_archive._dirs(args)
        self.assertEqual(refs_dir, self.plans)
        self.assertEqual(arch_dir, self.plans)


class ResolverMutationProbe(_RepositoryBackendFixture):
    """Falsifiable: with the layout-aware resolver reverted to the pre-fix legacy-only behavior,
    plans.scan finds nothing on a migrated repo (proving the fix is load-bearing)."""

    def test_reverting_resolver_breaks_migrated_scan(self):
        # Real resolver: finds the migrated plans.
        self.assertEqual(len(plans_mod.scan(self.repo)), 2)
        # Mutated resolver (pre-fix behavior: legacy .agents/<area> only) -> blind on migrated repo.
        with mock.patch.object(
            plans_mod,
            "_resolve_area_dir",
            lambda root, area: Path(root) / ".agents" / area,
        ):
            self.assertEqual(
                len(plans_mod.scan(self.repo)),
                0,
                "pre-fix legacy-only resolver should find nothing on a migrated repo",
            )


if __name__ == "__main__":
    unittest.main()
