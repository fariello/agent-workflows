"""Behavioral tests for the unified repo-relative POSIX path renderer.

Pins the fallback policy and caller parity across artifact_core, specs, check_engine,
artifact_rename, and doctor (IPD amt9fs, backlog qv0fi1).
"""

from __future__ import annotations

import os
import shutil
import tempfile
import unittest
from pathlib import Path

from agent_workflows import artifact_core as core
from agent_workflows import artifact_rename
from agent_workflows import check_engine
from agent_workflows import doctor
from agent_workflows import specs


def _safe_symlink(src: Path | str, dst: Path | str) -> None:
    try:
        os.symlink(src, dst)
    except (OSError, NotImplementedError) as exc:
        raise unittest.SkipTest(f"Symlinks not supported in this environment: {exc}")


class RepoRelativePosixPolicyTests(unittest.TestCase):
    """Pin the shared renderer's behavior across all 11 required policy cases."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.mkdtemp(prefix="aw_rel_posix_test_")
        self.repo_root = Path(self.temp_dir) / "repo"
        self.repo_root.mkdir(parents=True)
        self.outside_dir = Path(self.temp_dir) / "outside"
        self.outside_dir.mkdir(parents=True)

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_01_in_root_absolute_path(self) -> None:
        p = self.repo_root / "docs" / "guide.md"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("guide", encoding="utf-8")

        self.assertEqual(
            core.repo_relative_posix(str(p), self.repo_root), "docs/guide.md"
        )
        self.assertEqual(core.repo_relative_posix(p, self.repo_root), "docs/guide.md")

    def test_02_in_root_relative_path_including_dot_slash(self) -> None:
        self.assertEqual(
            core.repo_relative_posix("docs/guide.md", self.repo_root), "docs/guide.md"
        )
        self.assertEqual(
            core.repo_relative_posix("./docs/guide.md", self.repo_root), "docs/guide.md"
        )
        self.assertEqual(
            core.repo_relative_posix(Path("./docs/guide.md"), self.repo_root),
            "docs/guide.md",
        )

    def test_03_in_root_path_that_does_not_exist(self) -> None:
        p = self.repo_root / "missing" / "never_created.md"
        self.assertEqual(
            core.repo_relative_posix(str(p), self.repo_root), "missing/never_created.md"
        )
        self.assertEqual(
            core.repo_relative_posix("missing/never_created.md", self.repo_root),
            "missing/never_created.md",
        )

    def test_04_out_of_root_absolute_path_with_no_records_segment(self) -> None:
        p = self.outside_dir / "external.md"
        p.write_text("external", encoding="utf-8")
        self.assertEqual(
            core.repo_relative_posix(str(p), self.repo_root), "external.md"
        )
        self.assertEqual(core.repo_relative_posix(p, self.repo_root), "external.md")

    def test_05_out_of_root_absolute_path_under_records_segment(self) -> None:
        p_modern = (
            self.outside_dir
            / ".aw"
            / "records"
            / "specs"
            / "20261012-0001-01-ext.spec.md"
        )
        self.assertEqual(
            core.repo_relative_posix(str(p_modern), self.repo_root),
            ".aw/records/specs/20261012-0001-01-ext.spec.md",
        )
        self.assertEqual(
            core.repo_relative_posix(p_modern, self.repo_root),
            ".aw/records/specs/20261012-0001-01-ext.spec.md",
        )

        p_legacy = self.outside_dir / ".agents" / "docs" / "specs" / "leg.spec.md"
        self.assertEqual(
            core.repo_relative_posix(str(p_legacy), self.repo_root),
            ".agents/docs/specs/leg.spec.md",
        )

    def test_06_relative_path_escaping_the_root(self) -> None:
        self.assertEqual(
            core.repo_relative_posix("../outside.md", self.repo_root), "outside.md"
        )
        self.assertEqual(
            core.repo_relative_posix(Path("../outside.md"), self.repo_root),
            "outside.md",
        )
        self.assertEqual(
            core.repo_relative_posix("../../far_away.md", self.repo_root), "far_away.md"
        )

    def test_07_root_given_as_symlink_while_path_uses_real_spelling(self) -> None:
        real_root = Path(self.temp_dir) / "real_repo_07"
        sym_root = Path(self.temp_dir) / "sym_repo_07"
        real_root.mkdir(parents=True)
        _safe_symlink(real_root, sym_root)

        file_in_real = real_root / "src" / "main.py"
        file_in_real.parent.mkdir(parents=True, exist_ok=True)
        file_in_real.write_text("print('hello')", encoding="utf-8")

        self.assertEqual(
            core.repo_relative_posix(file_in_real, sym_root), "src/main.py"
        )
        self.assertEqual(
            core.repo_relative_posix(str(file_in_real), sym_root), "src/main.py"
        )

    def test_08_root_given_by_real_spelling_while_path_uses_symlink_spelling(
        self,
    ) -> None:
        real_root = Path(self.temp_dir) / "real_repo_08"
        sym_root = Path(self.temp_dir) / "sym_repo_08"
        real_root.mkdir(parents=True)
        _safe_symlink(real_root, sym_root)

        file_in_real = real_root / "src" / "main.py"
        file_in_real.parent.mkdir(parents=True, exist_ok=True)
        file_in_real.write_text("print('hello')", encoding="utf-8")

        file_via_sym = sym_root / "src" / "main.py"
        self.assertEqual(
            core.repo_relative_posix(file_via_sym, real_root), "src/main.py"
        )
        self.assertEqual(
            core.repo_relative_posix(str(file_via_sym), real_root), "src/main.py"
        )

    def test_09_in_root_symlinked_file_preserves_link_spelling(self) -> None:
        docs_dir = self.repo_root / "docs"
        docs_dir.mkdir(parents=True, exist_ok=True)
        target = docs_dir / "target.txt"
        target.write_text("target", encoding="utf-8")
        link_in_root = docs_dir / "link_in_root.txt"
        _safe_symlink(target, link_in_root)

        # Points at another in-root file: must return the link's relative path, not the target's
        self.assertEqual(
            core.repo_relative_posix(link_in_root, self.repo_root),
            "docs/link_in_root.txt",
        )
        self.assertEqual(
            core.repo_relative_posix(str(link_in_root), self.repo_root),
            "docs/link_in_root.txt",
        )

        # Points outside the root: must return the link's relative path, not the bare name (F-10)
        outside_target = self.outside_dir / "outside_target.txt"
        outside_target.write_text("outside", encoding="utf-8")
        link_outside = docs_dir / "link_outside.txt"
        _safe_symlink(outside_target, link_outside)

        self.assertEqual(
            core.repo_relative_posix(link_outside, self.repo_root),
            "docs/link_outside.txt",
        )
        self.assertEqual(
            core.repo_relative_posix(str(link_outside), self.repo_root),
            "docs/link_outside.txt",
        )

    def test_10_sentinel_and_empty_string(self) -> None:
        self.assertEqual(core.repo_relative_posix("<repo>", self.repo_root), "<repo>")
        self.assertEqual(
            core.repo_relative_posix("<custom_sentinel>", self.repo_root),
            "<custom_sentinel>",
        )
        self.assertEqual(core.repo_relative_posix("", self.repo_root), "")
        self.assertEqual(core.repo_relative_posix("<repo>", None), "<repo>")
        self.assertEqual(core.repo_relative_posix("", None), "")

    def test_11_specs_drift_location_cases_with_no_root(self) -> None:
        # Segment truncation of absolute path
        abs_seg = "/any/prefix/.aw/records/specs/20261012-0001-01-test.spec.md"
        self.assertEqual(
            core.repo_relative_posix(abs_seg),
            ".aw/records/specs/20261012-0001-01-test.spec.md",
        )

        # Segment truncation of relative path
        rel_seg = "sub/.aw/records/specs/20261012-0001-01-test.spec.md"
        self.assertEqual(
            core.repo_relative_posix(rel_seg),
            ".aw/records/specs/20261012-0001-01-test.spec.md",
        )

        # Unchanged relative path
        self.assertEqual(core.repo_relative_posix("docs/file.md"), "docs/file.md")
        self.assertEqual(core.repo_relative_posix("../file.md"), "../file.md")
        self.assertEqual(core.repo_relative_posix(Path("")), ".")


class RepoRelativePosixParityTests(unittest.TestCase):
    """Drive all four real callers on the same inputs to verify agreement and no root leaks."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.mkdtemp(prefix="aw_rel_posix_parity_")
        self.repo_root = Path(self.temp_dir) / "repo"
        self.plans_pending = self.repo_root / ".aw" / "records" / "plans" / "pending"
        self.plans_pending.mkdir(parents=True)
        self.outside_dir = Path(self.temp_dir) / "outside"
        self.outside_dir.mkdir(parents=True)

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_parity_in_root_path(self) -> None:
        p = self.plans_pending / "20261012-test-01-aaaaaa-test.ipd.md"
        p.write_text("# Plan", encoding="utf-8")

        r1 = check_engine._finding_rel_path(self.repo_root, p)
        r2 = artifact_rename._rel_to_repo(p, self.repo_root)
        r3 = doctor.build_remediation(
            core.Drift(str(p), "rule", "detail"), self.repo_root
        ).file_path

        expected = ".aw/records/plans/pending/20261012-test-01-aaaaaa-test.ipd.md"
        self.assertEqual(r1, expected)
        self.assertEqual(r2, expected)
        self.assertEqual(r3, expected)
        self.assertNotIn(str(self.repo_root), r1)
        self.assertNotIn(str(self.repo_root), r2)
        self.assertNotIn(str(self.repo_root), r3)

    def test_parity_out_of_root_path(self) -> None:
        p = self.outside_dir / "external.spec.md"
        p.write_text("# External", encoding="utf-8")

        r1 = check_engine._finding_rel_path(self.repo_root, p)
        r2 = artifact_rename._rel_to_repo(p, self.repo_root)
        r3 = doctor.build_remediation(
            core.Drift(str(p), "rule", "detail"), self.repo_root
        ).file_path

        expected = "external.spec.md"
        self.assertEqual(r1, expected)
        self.assertEqual(r2, expected)
        self.assertEqual(r3, expected)
        self.assertNotIn(str(self.temp_dir), r1)
        self.assertNotIn(str(self.temp_dir), r2)
        self.assertNotIn(str(self.temp_dir), r3)

    def test_parity_symlink_root_input(self) -> None:
        real_root = Path(self.temp_dir) / "real_repo_parity"
        sym_root = Path(self.temp_dir) / "sym_repo_parity"
        plans_dir = real_root / ".aw" / "records" / "plans" / "pending"
        plans_dir.mkdir(parents=True)
        plan_file = plans_dir / "20261012-test-01-bbbbbb-sym.ipd.md"
        plan_file.write_text("# Plan", encoding="utf-8")
        _safe_symlink(real_root, sym_root)

        r1 = check_engine._finding_rel_path(sym_root, plan_file)
        r2 = artifact_rename._rel_to_repo(plan_file, sym_root)
        r3 = doctor.build_remediation(
            core.Drift(str(plan_file), "rule", "detail"), sym_root
        ).file_path

        expected = ".aw/records/plans/pending/20261012-test-01-bbbbbb-sym.ipd.md"
        self.assertEqual(r1, expected)
        self.assertEqual(r2, expected)
        self.assertEqual(r3, expected)
        self.assertNotIn(str(self.temp_dir), r1)
        self.assertNotIn(str(self.temp_dir), r2)
        self.assertNotIn(str(self.temp_dir), r3)

    def test_parity_in_root_symlinked_file(self) -> None:
        target = self.plans_pending / "20261012-test-01-cccccc-target.ipd.md"
        target.write_text("# Target", encoding="utf-8")
        link = self.plans_pending / "20261012-test-01-cccccc-link.ipd.md"
        _safe_symlink(target, link)

        r1 = check_engine._finding_rel_path(self.repo_root, link)
        r2 = artifact_rename._rel_to_repo(link, self.repo_root)
        r3 = doctor.build_remediation(
            core.Drift(str(link), "rule", "detail"), self.repo_root
        ).file_path

        expected = ".aw/records/plans/pending/20261012-test-01-cccccc-link.ipd.md"
        self.assertEqual(r1, expected)
        self.assertEqual(r2, expected)
        self.assertEqual(r3, expected)
        self.assertNotIn(str(self.repo_root), r1)
        self.assertNotIn(str(self.repo_root), r2)
        self.assertNotIn(str(self.repo_root), r3)

    def test_parity_in_root_symlinked_file_pointing_outside(self) -> None:
        outside_target = self.outside_dir / "target.md"
        outside_target.write_text("# Target", encoding="utf-8")
        link_outside = self.repo_root / "lnk.md"
        _safe_symlink(outside_target, link_outside)

        r1 = check_engine._finding_rel_path(self.repo_root, link_outside)
        r2 = artifact_rename._rel_to_repo(link_outside, self.repo_root)
        r3 = doctor.build_remediation(
            core.Drift(str(link_outside), "rule", "detail"), self.repo_root
        ).file_path

        expected = "lnk.md"
        self.assertEqual(r1, expected)
        self.assertEqual(r2, expected)
        self.assertEqual(r3, expected)
        self.assertNotIn(str(self.temp_dir), r1)
        self.assertNotIn(str(self.temp_dir), r2)
        self.assertNotIn(str(self.temp_dir), r3)

    def test_parity_root_less_inputs_with_specs_validate_spec(self) -> None:
        spec_text = (
            "# Spec: Parity\n\n- Status: invalid_status\n- Id: 123456\n\n"
            "## Workflow history\n- 2026-01-01 draft (t): created.\n"
        )

        # 1. Truncated segment (modern layout)
        p_modern = (
            Path(self.temp_dir)
            / "outside"
            / ".aw"
            / "records"
            / "specs"
            / "20261012-123456-01-123456-test.spec.md"
        )
        drifts_modern = specs.validate_spec(p_modern, spec_text)
        self.assertTrue(drifts_modern)
        self.assertEqual(
            drifts_modern[0].location,
            ".aw/records/specs/20261012-123456-01-123456-test.spec.md",
        )
        self.assertEqual(
            drifts_modern[0].location,
            core.repo_relative_posix(p_modern),
        )
        self.assertNotIn(str(self.temp_dir), drifts_modern[0].location)

        # 2. Bare name fallback for outside file with no records segment
        p_bare = Path(self.temp_dir) / "outside" / "test.spec.md"
        drifts_bare = specs.validate_spec(p_bare, spec_text)
        self.assertTrue(drifts_bare)
        self.assertEqual(drifts_bare[0].location, "test.spec.md")
        self.assertEqual(drifts_bare[0].location, core.repo_relative_posix(p_bare))
        self.assertNotIn(str(self.temp_dir), drifts_bare[0].location)

        # 3. Already relative path
        p_rel = Path("test.spec.md")
        drifts_rel = specs.validate_spec(p_rel, spec_text)
        self.assertTrue(drifts_rel)
        self.assertEqual(drifts_rel[0].location, "test.spec.md")
        self.assertEqual(drifts_rel[0].location, core.repo_relative_posix(p_rel))
