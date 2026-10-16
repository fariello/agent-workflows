"""Behavioral tests for the unified repo-relative POSIX path renderer.

Pins the fallback policy and caller parity across artifact_core, specs, check_engine,
artifact_rename, and doctor (IPD amt9fs, backlog qv0fi1).
"""

from __future__ import annotations

import argparse
import io
import os
import shutil
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

from agent_workflows import artifact_core as core
from agent_workflows import artifact_rename
from agent_workflows import attention
from agent_workflows import check_engine
from agent_workflows import doctor
from agent_workflows import ipd_lifecycle
from agent_workflows import layout_inventory
from agent_workflows import specs
from tests import support


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
        r4 = ipd_lifecycle._repo_relative(self.repo_root, p)
        r5 = attention._rel_posix(self.repo_root, p)
        with mock.patch.object(
            check_engine,
            "check_collisions",
            lambda *a, **k: [core.Drift(str(p), "check.x", "d")],
        ):
            doc_res = doctor.probe_artifacts(self.repo_root)
            r6 = [
                d
                for d in (doc_res.all_drift + doc_res.executed_warnings)
                if d.rule == "check.x"
            ][0].location

        expected = ".aw/records/plans/pending/20261012-test-01-aaaaaa-test.ipd.md"
        self.assertEqual(r1, expected)
        self.assertEqual(r2, expected)
        self.assertEqual(r3, expected)
        self.assertEqual(r4, expected)
        self.assertEqual(r5, expected)
        self.assertEqual(r6, expected)
        self.assertNotIn(str(self.repo_root), r1)
        self.assertNotIn(str(self.repo_root), r2)
        self.assertNotIn(str(self.repo_root), r3)
        self.assertNotIn(str(self.repo_root), r4)
        self.assertNotIn(str(self.repo_root), r5)
        self.assertNotIn(str(self.repo_root), r6)

    def test_parity_out_of_root_path(self) -> None:
        p = self.outside_dir / "external.spec.md"
        p.write_text("# External", encoding="utf-8")

        r1 = check_engine._finding_rel_path(self.repo_root, p)
        r2 = artifact_rename._rel_to_repo(p, self.repo_root)
        r3 = doctor.build_remediation(
            core.Drift(str(p), "rule", "detail"), self.repo_root
        ).file_path
        r4 = ipd_lifecycle._repo_relative(self.repo_root, p)
        r5 = attention._rel_posix(self.repo_root, p)
        with mock.patch.object(
            check_engine,
            "check_collisions",
            lambda *a, **k: [core.Drift(str(p), "check.x", "d")],
        ):
            doc_res = doctor.probe_artifacts(self.repo_root)
            r6 = [
                d
                for d in (doc_res.all_drift + doc_res.executed_warnings)
                if d.rule == "check.x"
            ][0].location

        expected = "external.spec.md"
        self.assertEqual(r1, expected)
        self.assertEqual(r2, expected)
        self.assertEqual(r3, expected)
        self.assertEqual(r4, expected)
        self.assertEqual(r5, expected)
        self.assertEqual(r6, expected)
        self.assertNotIn(str(self.temp_dir), r1)
        self.assertNotIn(str(self.temp_dir), r2)
        self.assertNotIn(str(self.temp_dir), r3)
        self.assertNotIn(str(self.temp_dir), r4)
        self.assertNotIn(str(self.temp_dir), r5)
        self.assertNotIn(str(self.temp_dir), r6)

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
        r4 = ipd_lifecycle._repo_relative(sym_root, plan_file)
        r5 = attention._rel_posix(sym_root, plan_file)
        with mock.patch.object(
            check_engine,
            "check_collisions",
            lambda *a, **k: [core.Drift(str(plan_file), "check.x", "d")],
        ):
            doc_res = doctor.probe_artifacts(sym_root)
            r6 = [
                d
                for d in (doc_res.all_drift + doc_res.executed_warnings)
                if d.rule == "check.x"
            ][0].location

        expected = ".aw/records/plans/pending/20261012-test-01-bbbbbb-sym.ipd.md"
        self.assertEqual(r1, expected)
        self.assertEqual(r2, expected)
        self.assertEqual(r3, expected)
        self.assertEqual(r4, expected)
        self.assertEqual(r5, expected)
        self.assertEqual(r6, expected)
        self.assertNotIn(str(self.temp_dir), r1)
        self.assertNotIn(str(self.temp_dir), r2)
        self.assertNotIn(str(self.temp_dir), r3)
        self.assertNotIn(str(self.temp_dir), r4)
        self.assertNotIn(str(self.temp_dir), r5)
        self.assertNotIn(str(self.temp_dir), r6)

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
        r4 = ipd_lifecycle._repo_relative(self.repo_root, link)
        r5 = attention._rel_posix(self.repo_root, link)
        with mock.patch.object(
            check_engine,
            "check_collisions",
            lambda *a, **k: [core.Drift(str(link), "check.x", "d")],
        ):
            doc_res = doctor.probe_artifacts(self.repo_root)
            r6 = [
                d
                for d in (doc_res.all_drift + doc_res.executed_warnings)
                if d.rule == "check.x"
            ][0].location

        expected = ".aw/records/plans/pending/20261012-test-01-cccccc-link.ipd.md"
        self.assertEqual(r1, expected)
        self.assertEqual(r2, expected)
        self.assertEqual(r3, expected)
        self.assertEqual(r4, expected)
        self.assertEqual(r5, expected)
        self.assertEqual(r6, expected)
        self.assertNotIn(str(self.repo_root), r1)
        self.assertNotIn(str(self.repo_root), r2)
        self.assertNotIn(str(self.repo_root), r3)
        self.assertNotIn(str(self.repo_root), r4)
        self.assertNotIn(str(self.repo_root), r5)
        self.assertNotIn(str(self.repo_root), r6)

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
        r4 = ipd_lifecycle._repo_relative(self.repo_root, link_outside)
        r5 = attention._rel_posix(self.repo_root, link_outside)
        with mock.patch.object(
            check_engine,
            "check_collisions",
            lambda *a, **k: [core.Drift(str(link_outside), "check.x", "d")],
        ):
            doc_res = doctor.probe_artifacts(self.repo_root)
            r6 = [
                d
                for d in (doc_res.all_drift + doc_res.executed_warnings)
                if d.rule == "check.x"
            ][0].location

        expected = "lnk.md"
        self.assertEqual(r1, expected)
        self.assertEqual(r2, expected)
        self.assertEqual(r3, expected)
        self.assertEqual(r4, expected)
        self.assertEqual(r5, expected)
        self.assertEqual(r6, expected)
        self.assertNotIn(str(self.temp_dir), r1)
        self.assertNotIn(str(self.temp_dir), r2)
        self.assertNotIn(str(self.temp_dir), r3)
        self.assertNotIn(str(self.temp_dir), r4)
        self.assertNotIn(str(self.temp_dir), r5)
        self.assertNotIn(str(self.temp_dir), r6)

    def test_attention_item_for_path_and_relative_input_outside_cwd(self) -> None:
        out_of_root_path = self.outside_dir / "external.ipd.md"
        out_of_root_path.write_text("# External", encoding="utf-8")
        item = attention.item_for_path(out_of_root_path, repo_root=self.repo_root)
        self.assertIsNone(item)

        orig_cwd = os.getcwd()
        try:
            os.chdir(self.outside_dir)
            rel_plan = Path(
                ".aw/records/plans/pending/20261012-test-01-aaaaaa-in.ipd.md"
            )
            rendered = attention._rel_posix(self.repo_root, rel_plan)
            self.assertEqual(
                rendered,
                ".aw/records/plans/pending/20261012-test-01-aaaaaa-in.ipd.md",
            )
        finally:
            os.chdir(orig_cwd)

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


class LayoutInventoryRepoRelativeContractTests(unittest.TestCase):
    """Pin the distinct Optional[str] and symlink-preserving contract of layout_inventory._repo_relative."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.mkdtemp(prefix="aw_layout_inv_contract_")
        self.repo_root = Path(self.temp_dir) / "repo"
        self.repo_root.mkdir(parents=True)
        self.outside_dir = Path(self.temp_dir) / "outside"
        self.outside_dir.mkdir(parents=True)
        subprocess.run(
            ["git", "init", "-q", "-b", "main"], cwd=self.repo_root, check=True
        )
        subprocess.run(
            ["git", "config", "user.email", "t@e.com"], cwd=self.repo_root, check=True
        )
        subprocess.run(
            ["git", "config", "user.name", "T"], cwd=self.repo_root, check=True
        )

        outside_file = self.outside_dir / "external.txt"
        outside_file.write_text("external content", encoding="utf-8")

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_layout_inventory_repo_relative_and_external_inventory_contract(
        self,
    ) -> None:
        outside_file = self.outside_dir / "external.txt"
        # 1. layout_inventory._repo_relative returns None for outside path
        self.assertIsNone(layout_inventory._repo_relative(outside_file, self.repo_root))

        # 2. layout_inventory.inventory with external root
        inv = layout_inventory.inventory(
            self.repo_root, [("ext", self.outside_dir)], include_paths=False
        )
        self.assertEqual(len(inv["roots"]), 1)
        root_doc = inv["roots"][0]
        self.assertFalse(root_doc["within_repo"])

        items = [i for i in inv["items"] if i["source_relpath"] == "external.txt"]
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["git_state"], "external")
        self.assertIsNone(items[0]["repo_relpath"])

        # 3. in-repo symlink pointing to outside_dir
        link_dir = self.repo_root / "links"
        link_dir.mkdir(parents=True, exist_ok=True)
        link_path = link_dir / "link_to_outside"
        _safe_symlink(self.outside_dir, link_path)

        inv_links = layout_inventory.inventory(
            self.repo_root, [("links", link_dir)], include_paths=False
        )
        symlink_items = [
            i for i in inv_links["items"] if i["source_relpath"] == "link_to_outside"
        ]
        self.assertEqual(len(symlink_items), 1)
        self.assertEqual(symlink_items[0]["kind"], "symlink")
        self.assertEqual(symlink_items[0]["repo_relpath"], "links/link_to_outside")


class IpdLifecycleOutOfRootPlanRefusalTests(unittest.TestCase):
    """Pin the out-of-root plan containment refusal in run_begin and run_finalize (E-06)."""

    def setUp(self) -> None:
        support.declare_execution_role(self)
        self.temp_dir = tempfile.mkdtemp(prefix="aw_ipd_out_of_root_")
        self.root_a = Path(self.temp_dir) / "repo_a"
        self.root_b = Path(self.temp_dir) / "repo_b"
        self._init_git(self.root_a)
        self._init_git(self.root_b)

        self.plan_filename = "20261012-demo-01-abc123-demo.ipd.md"
        plan_text_a = support.ready_plan_text(plan_id="abc123", title="plan in repo a")
        plan_text_b = support.ready_plan_text(plan_id="abc123", title="plan in repo b")

        self.plan_a = self._write_plan(self.root_a, plan_text_a, self.plan_filename)
        self.plan_b = self._write_plan(self.root_b, plan_text_b, self.plan_filename)
        self._commit_all(self.root_a, "init a")
        self._commit_all(self.root_b, "init b")

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _init_git(self, root: Path) -> None:
        root.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "init", "-q", "-b", "main"], cwd=root, check=True)
        subprocess.run(["git", "config", "user.email", "t@e.com"], cwd=root, check=True)
        subprocess.run(["git", "config", "user.name", "T"], cwd=root, check=True)
        (root / ".gitignore").write_text(".aw/state/\n", encoding="utf-8")

    def _commit_all(self, root: Path, msg: str) -> None:
        subprocess.run(["git", "add", "-A"], cwd=root, check=True)
        subprocess.run(["git", "commit", "-q", "-m", msg], cwd=root, check=True)

    def _write_plan(self, root: Path, text: str, name: str) -> Path:
        d = root / ".aw" / "records" / "plans" / "pending"
        d.mkdir(parents=True, exist_ok=True)
        p = d / name
        p.write_text(text, encoding="utf-8")
        return p

    def test_run_begin_out_of_root_plan_refused(self) -> None:
        initial_bytes_a = self.plan_a.read_bytes()
        ns = argparse.Namespace(
            plan=str(self.plan_b.resolve()),
            actor="tester",
            dir=str(self.root_a),
            agent=False,
            json=False,
            no_color=True,
        )
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = ipd_lifecycle.run_begin(ns)
        self.assertEqual(rc, ipd_lifecycle.EXIT_CANNOT_RUN)
        self.assertEqual(self.plan_a.read_bytes(), initial_bytes_a)
        rcpt = ipd_lifecycle.receipt_path_for(self.root_a, "abc123")
        self.assertFalse(rcpt.is_file())

    def test_run_finalize_out_of_root_plan_refused(self) -> None:
        initial_bytes_a = self.plan_a.read_bytes()
        ns = argparse.Namespace(
            plan=str(self.plan_b.resolve()),
            actor="tester",
            message="finalize demo",
            apply=True,
            dir=str(self.root_a),
            agent=False,
            json=False,
            no_color=True,
        )
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = ipd_lifecycle.run_finalize(ns)
        self.assertEqual(rc, ipd_lifecycle.EXIT_CANNOT_RUN)
        self.assertEqual(self.plan_a.read_bytes(), initial_bytes_a)
        rcpt = ipd_lifecycle.receipt_path_for(self.root_a, "abc123")
        self.assertFalse(rcpt.is_file())
