"""Tests for artifact_core.git_mv and engine._git_mv repository containment (IPD 7sy2gm).

Covers:
- E-01 / V-01: MoveOutsideRepositoryError and boundary-crossing containment guard in artifact_core.git_mv.
- E-02 / V-02: Delegation of engine._git_mv to artifact_core.git_mv.
- E-03 / V-03: Cases (a) through (g):
  (a) tracked source with ../ escaping destination raises MoveOutsideRepositoryError;
  (b) absolute destination outside repo raises MoveOutsideRepositoryError;
  (c) source outside repo with in-repo destination raises MoveOutsideRepositoryError;
  (c2) source and destination both outside repo (companion layout) succeed without raising;
  (d) destination under in-repo symlink pointing outside raises MoveOutsideRepositoryError;
  (e) untracked in-repo source moved to new in-repo subdir via fallback;
  (f) tracked in-repo move staged as rename (git status shows R);
  (g) end-to-end companion backend flow (aw specs new + aw set to-review).
"""

from __future__ import annotations

import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from contextlib import redirect_stderr, redirect_stdout

from agent_workflows import artifact_core
from agent_workflows import cli
from agent_workflows import engine

try:
    from agent_workflows.artifact_core import MoveOutsideRepositoryError
except ImportError:  # pragma: no cover

    class MoveOutsideRepositoryError(Exception):  # type: ignore[no-redef]
        """Fallback definition so test collection succeeds when verifying discriminator behavior."""


class TestArtifactCoreGitMvContainment(unittest.TestCase):
    """Base test case for repository boundary containment in git_mv."""

    def setUp(self):
        self.tmp_base = Path(
            tempfile.mkdtemp(prefix="aw_test_git_mv_containment_")
        ).resolve()
        self.addCleanup(lambda: shutil.rmtree(self.tmp_base, ignore_errors=True))

        self.repo_dir = self.tmp_base / "n1" / "n2" / "n3" / "repo"
        self.repo_dir.mkdir(parents=True, exist_ok=True)

        self.env_patcher = patch.dict(
            os.environ,
            {
                "HOME": str(self.tmp_base),
                "XDG_CONFIG_HOME": str(self.tmp_base),
            },
        )
        self.env_patcher.start()
        self.addCleanup(self.env_patcher.stop)

        subprocess.run(["git", "init", "-q"], cwd=self.repo_dir, check=True)
        subprocess.run(
            ["git", "config", "user.email", "t@e.com"], cwd=self.repo_dir, check=True
        )
        subprocess.run(
            ["git", "config", "user.name", "T"], cwd=self.repo_dir, check=True
        )

    def test_case_a_tracked_escape_relative_destination_refused(self):
        """Case (a): tracked source with ../ escaping destination raises MoveOutsideRepositoryError,
        source remains on disk, git status --short is empty, and no file or directory was created
        anywhere under temp base outside repo.
        """
        sub_dir = self.repo_dir / "sub"
        sub_dir.mkdir()
        src_file = sub_dir / "tracked.md"
        src_file.write_text("tracked content\n", encoding="utf-8")
        subprocess.run(["git", "add", "sub/tracked.md"], cwd=self.repo_dir, check=True)
        subprocess.run(
            ["git", "commit", "-m", "add tracked.md"], cwd=self.repo_dir, check=True
        )

        before_paths = set(self.tmp_base.rglob("*"))

        escape_dst = "sub/../../../../escaped.md"
        target_outside = (self.repo_dir / escape_dst).resolve()
        self.assertNotIn(str(self.repo_dir), str(target_outside))

        with self.assertRaises(MoveOutsideRepositoryError):
            artifact_core.git_mv(self.repo_dir, "sub/tracked.md", escape_dst)

        self.assertTrue(src_file.exists())
        self.assertEqual(src_file.read_text(encoding="utf-8"), "tracked content\n")

        status = subprocess.run(
            ["git", "status", "--short"],
            cwd=self.repo_dir,
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertEqual(status.stdout.strip(), "")

        after_paths = set(self.tmp_base.rglob("*"))
        new_paths_outside_repo = {
            p
            for p in (after_paths - before_paths)
            if not str(p).startswith(str(self.repo_dir))
        }
        self.assertEqual(new_paths_outside_repo, set())

    def test_case_a_engine_git_mv_delegation_refuses_escape(self):
        """Case (a) variant: engine._git_mv delegates to artifact_core.git_mv and refuses escape."""
        sub_dir = self.repo_dir / "sub_engine"
        sub_dir.mkdir()
        src_file = sub_dir / "engine_tracked.md"
        src_file.write_text("engine content\n", encoding="utf-8")
        subprocess.run(
            ["git", "add", "sub_engine/engine_tracked.md"],
            cwd=self.repo_dir,
            check=True,
        )
        subprocess.run(
            ["git", "commit", "-m", "add engine_tracked.md"],
            cwd=self.repo_dir,
            check=True,
        )

        escape_dst = "sub_engine/../../../../engine_escaped.md"
        with self.assertRaises(MoveOutsideRepositoryError):
            engine._git_mv(self.repo_dir, "sub_engine/engine_tracked.md", escape_dst)

        self.assertTrue(src_file.exists())
        status = subprocess.run(
            ["git", "status", "--short"],
            cwd=self.repo_dir,
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertEqual(status.stdout.strip(), "")

    def test_case_b_absolute_destination_outside_repo_refused(self):
        """Case (b): absolute destination outside repo raises MoveOutsideRepositoryError,
        source intact, git status clean, and destination was not created.
        """
        sub_dir = self.repo_dir / "sub"
        sub_dir.mkdir(exist_ok=True)
        src_file = sub_dir / "tracked_b.md"
        src_file.write_text("tracked b\n", encoding="utf-8")
        subprocess.run(
            ["git", "add", "sub/tracked_b.md"], cwd=self.repo_dir, check=True
        )
        subprocess.run(
            ["git", "commit", "-m", "add tracked_b.md"], cwd=self.repo_dir, check=True
        )

        abs_dst = self.tmp_base / "outside_dir" / "abs_escape.md"
        with self.assertRaises(MoveOutsideRepositoryError):
            artifact_core.git_mv(self.repo_dir, "sub/tracked_b.md", str(abs_dst))

        self.assertTrue(src_file.exists())
        self.assertFalse(abs_dst.exists())
        self.assertFalse(abs_dst.parent.exists())

        status = subprocess.run(
            ["git", "status", "--short"],
            cwd=self.repo_dir,
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertEqual(status.stdout.strip(), "")

    def test_case_c_source_outside_repo_refused(self):
        """Case (c): source outside the repo with in-repo destination raises MoveOutsideRepositoryError."""
        outside_src = self.tmp_base / "outside_src.md"
        outside_src.write_text("outside data\n", encoding="utf-8")

        dst_rel = "sub/imported.md"
        with self.assertRaises(MoveOutsideRepositoryError):
            artifact_core.git_mv(self.repo_dir, str(outside_src), dst_rel)

        self.assertTrue(outside_src.exists())
        self.assertFalse((self.repo_dir / dst_rel).exists())
        status = subprocess.run(
            ["git", "status", "--short"],
            cwd=self.repo_dir,
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertEqual(status.stdout.strip(), "")

    def test_case_c2_both_outside_repo_allowed(self):
        """Case (c2): source AND destination both outside the repo (companion layout)
        do NOT raise and the file is moved.
        """
        comp_records = self.tmp_base / "n1" / "n2" / "n3" / "repo.aw" / "records"
        draft_dir = comp_records / "specs" / "draft"
        to_review_dir = comp_records / "specs" / "to-review"
        draft_dir.mkdir(parents=True, exist_ok=True)

        src_file = draft_dir / "20261012-test-01-c2test-demo.spec.md"
        src_file.write_text("spec content\n", encoding="utf-8")
        dst_file = to_review_dir / "20261012-test-01-c2test-demo.spec.md"

        artifact_core.git_mv(self.repo_dir, str(src_file), str(dst_file))

        self.assertFalse(src_file.exists())
        self.assertTrue(dst_file.exists())
        self.assertEqual(dst_file.read_text(encoding="utf-8"), "spec content\n")

    def test_case_d_symlink_destination_pointing_outside_refused(self):
        """Case (d): destination under an in-repo symlink pointing outside raises MoveOutsideRepositoryError."""
        if not hasattr(os, "symlink"):
            self.skipTest("Symlinks not supported on this platform")

        outside_dir = self.tmp_base / "outside_sym_target"
        outside_dir.mkdir(exist_ok=True)

        symlink_path = self.repo_dir / "ext_link"
        try:
            symlink_path.symlink_to(outside_dir)
        except OSError:
            self.skipTest("Cannot create symlinks in this environment")

        sub_dir = self.repo_dir / "sub"
        sub_dir.mkdir(exist_ok=True)
        src_file = sub_dir / "tracked_d.md"
        src_file.write_text("tracked d\n", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=self.repo_dir, check=True)
        subprocess.run(
            ["git", "commit", "-m", "add symlink and tracked_d.md"],
            cwd=self.repo_dir,
            check=True,
        )

        symlink_dst = "ext_link/nested/escape.md"
        with self.assertRaises(MoveOutsideRepositoryError):
            artifact_core.git_mv(self.repo_dir, "sub/tracked_d.md", symlink_dst)

        self.assertTrue(src_file.exists())
        self.assertFalse((outside_dir / "nested").exists())
        self.assertFalse((outside_dir / "nested" / "escape.md").exists())

    def test_case_e_untracked_in_repo_source_fallback_preserved(self):
        """Case (e): untracked in-repo source is still moved into a new in-repo subdirectory (fallback preserved)."""
        src_file = self.repo_dir / "untracked.md"
        src_file.write_text("untracked payload\n", encoding="utf-8")

        dst_rel = "new_sub/untracked_moved.md"
        artifact_core.git_mv(self.repo_dir, "untracked.md", dst_rel)

        self.assertFalse(src_file.exists())
        dst_file = self.repo_dir / dst_rel
        self.assertTrue(dst_file.exists())
        self.assertEqual(dst_file.read_text(encoding="utf-8"), "untracked payload\n")

    def test_case_f_tracked_in_repo_move_staged_as_rename(self):
        """Case (f): tracked in-repo move is staged as a rename (git status --short shows R)."""
        src_file = self.repo_dir / "rename_source.md"
        src_file.write_text("rename me\n", encoding="utf-8")
        subprocess.run(
            ["git", "add", "rename_source.md"], cwd=self.repo_dir, check=True
        )
        subprocess.run(
            ["git", "commit", "-m", "add rename_source.md"],
            cwd=self.repo_dir,
            check=True,
        )

        artifact_core.git_mv(self.repo_dir, "rename_source.md", "rename_dest.md")

        self.assertFalse(src_file.exists())
        self.assertTrue((self.repo_dir / "rename_dest.md").exists())

        status = subprocess.run(
            ["git", "status", "--short"],
            cwd=self.repo_dir,
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertIn("R  rename_source.md -> rename_dest.md", status.stdout)

    def test_case_g_companion_backend_end_to_end(self):
        """Case (g) END-TO-END: in a scratch repo whose .aw/config/project.json sets
        {"records_backend": "companion"} (with HOME and XDG_CONFIG_HOME pinned to temp base),
        aw specs new --title T --slug t --apply then aw set to-review <spec> --no-commit
        driven through cli.main exits 0 and the spec lands under the companion specs/to-review/ directory.
        """
        comp_repo = self.tmp_base / "comp_repo"
        comp_repo.mkdir()
        cfg_dir = comp_repo / ".aw" / "config"
        cfg_dir.mkdir(parents=True)
        (cfg_dir / "project.json").write_text(
            json.dumps({"records_backend": "companion"}), encoding="utf-8"
        )
        subprocess.run(["git", "init", "-q"], cwd=comp_repo, check=True)
        subprocess.run(
            ["git", "config", "user.email", "t@e.com"], cwd=comp_repo, check=True
        )
        subprocess.run(["git", "config", "user.name", "T"], cwd=comp_repo, check=True)

        out_new, err_new = io.StringIO(), io.StringIO()
        with redirect_stdout(out_new), redirect_stderr(err_new):
            rc_new = cli.main(
                [
                    "specs",
                    "new",
                    "--title",
                    "T",
                    "--slug",
                    "t",
                    "--apply",
                    "--dir",
                    str(comp_repo),
                ]
            )
        self.assertEqual(
            rc_new,
            0,
            f"specs new failed: {out_new.getvalue()} {err_new.getvalue()}",
        )

        comp_specs_dir = self.tmp_base / "comp_repo.aw" / "records" / "specs"
        draft_specs = list((comp_specs_dir / "draft").glob("*.spec.md"))
        self.assertEqual(len(draft_specs), 1)
        spec_path = draft_specs[0]

        out_set, err_set = io.StringIO(), io.StringIO()
        with redirect_stdout(out_set), redirect_stderr(err_set):
            rc_set = cli.main(
                [
                    "set",
                    "to-review",
                    str(spec_path),
                    "--no-commit",
                    "--dir",
                    str(comp_repo),
                ]
            )
        self.assertEqual(
            rc_set,
            0,
            f"set to-review failed: {out_set.getvalue()} {err_set.getvalue()}",
        )

        to_review_specs = list((comp_specs_dir / "to-review").glob("*.spec.md"))
        self.assertEqual(len(to_review_specs), 1)
        self.assertEqual(to_review_specs[0].name, spec_path.name)
        self.assertFalse(spec_path.exists())

    def test_destination_resolves_to_repo_root_refused(self):
        """Destination resolving to repo root itself raises MoveOutsideRepositoryError."""
        sub_dir = self.repo_dir / "sub"
        sub_dir.mkdir(exist_ok=True)
        src_file = sub_dir / "root_test.md"
        src_file.write_text("root test\n", encoding="utf-8")
        subprocess.run(
            ["git", "add", "sub/root_test.md"], cwd=self.repo_dir, check=True
        )
        subprocess.run(
            ["git", "commit", "-m", "add root_test.md"],
            cwd=self.repo_dir,
            check=True,
        )

        with self.assertRaises(MoveOutsideRepositoryError):
            artifact_core.git_mv(self.repo_dir, "sub/root_test.md", ".")
