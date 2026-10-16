"""Regression test suite for nonsurveyable_root_refusal (IPD dirsilent-01 i6mby8).

Pins the pure refusal primitive in `project_context` directly in process against
tempfile fixtures constructed outside any AW project.

Pins:
- Precondition: find_project_root is None for no-project fixtures.
- All four message cases:
  (a) real project root (may_proceed=True, no human text, no summary, no next action)
  (b) subdirectory of real project with explicit --dir (may_proceed=False, human text
      names enclosing root and literal aw <verb> --dir <root>, summary equals shipped
      inside-project string, next_action is None)
  (c) directory in no project and no git repo with explicit --dir (may_proceed=False,
      summary equals shipped no-project-at-specified-directory string, next_action is None)
  (d) directory in no AW project but inside a git repository with explicit --dir
      (may_proceed=False, summary equals shipped no-project-at-specified-directory string,
      next_action is literal aw install . with shipped description)
- Non-explicit variants of (c) and (d) (bare-cwd climb failed):
  summary equals shipped bare-cwd string ("... at the working directory or any ancestor ..."),
  with next_action preserved for (d).
- F-14 negatives on case (b):
  human text does not contain "is not installed in it", and next-action is not "aw install .".
- Path-freeness for all machine strings:
  neither fixture temp paths nor found root appears in summary or next-action.
- Purity and silence:
  recursive file inventories identical before/after, and stdout/stderr empty.
- Outcomes-not-structure:
  exercises observable return values and side effects only; no AST/inspect/regex on code.
"""

from __future__ import annotations

import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import unittest.mock

from agent_workflows.project_context import (
    ProjectLocationCase,
    RootRefusal,
    classify_project_dir,
    find_project_root,
    git_root_for_message,
    is_project_dir,
    nonsurveyable_root_refusal,
)


def _file_tree_snapshot(root: Path) -> dict[str, int]:
    """Capture a recursive snapshot of all file paths and sizes under root."""
    snapshot: dict[str, int] = {}
    for p in root.rglob("*"):
        if p.is_file():
            snapshot[str(p.relative_to(root))] = p.stat().st_size
    return snapshot


class NonsurveyableRootRefusalTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir_obj = tempfile.TemporaryDirectory()
        self.fix_root = Path(self.temp_dir_obj.name).resolve()

        # 1. Real AW project with git initialized and durable records dir
        self.real_proj = self.fix_root / "real_project"
        self.real_proj.mkdir(parents=True)
        (self.real_proj / ".aw" / "records" / "specs" / "draft").mkdir(parents=True)
        subprocess.run(
            ["git", "init", str(self.real_proj)],
            check=True,
            capture_output=True,
        )

        # 2. Deep subdirectory within the real AW project
        self.deep_subdir = self.real_proj / "src" / "deep"
        self.deep_subdir.mkdir(parents=True)

        # 3. Directory with no AW project and NOT in a git repo
        self.nongit_dir = self.fix_root / "nongit"
        self.nongit_dir.mkdir(parents=True)

        # 4. Git repository without AW project
        self.git_no_aw = self.fix_root / "git_no_aw"
        self.git_no_aw.mkdir(parents=True)
        subprocess.run(
            ["git", "init", str(self.git_no_aw)],
            check=True,
            capture_output=True,
        )

    def tearDown(self):
        self.temp_dir_obj.cleanup()

    def test_fixture_preconditions(self):
        """Precondition: no-project fixtures must have find_project_root == None."""
        self.assertIsNone(
            find_project_root(self.fix_root),
            "tempfile root itself must not be under an AW project",
        )
        self.assertIsNone(
            find_project_root(self.nongit_dir),
            "nongit_dir must not be under an AW project",
        )
        self.assertIsNone(
            find_project_root(self.git_no_aw),
            "git_no_aw must not be under an AW project",
        )
        self.assertTrue(
            is_project_dir(self.real_proj),
            "real_proj must be detected as an AW project root",
        )
        self.assertFalse(
            is_project_dir(self.deep_subdir),
            "deep_subdir must not be detected as an AW project root",
        )
        self.assertEqual(
            find_project_root(self.deep_subdir),
            self.real_proj,
            "deep_subdir must find real_proj as enclosing project root",
        )
        self.assertFalse(
            is_project_dir(self.nongit_dir),
            "nongit_dir must not be detected as an AW project root",
        )
        self.assertFalse(
            is_project_dir(self.git_no_aw),
            "git_no_aw must not be detected as an AW project root",
        )

    def test_case_a_real_project_root(self):
        """Case (a): The resolved root IS a project root -> may_proceed=True."""
        refusal = nonsurveyable_root_refusal(
            verb="attention",
            repo_root=self.real_proj,
            explicit_dir=True,
        )
        self.assertIsInstance(refusal, RootRefusal)
        self.assertTrue(refusal.may_proceed)
        self.assertTrue(refusal.can_proceed)
        self.assertIsNone(refusal.human_message)
        self.assertIsNone(refusal.human_text)
        self.assertIsNone(refusal.message)
        self.assertIsNone(refusal.summary)
        self.assertIsNone(refusal.next_action)
        self.assertIsNone(refusal.next_action_command)
        self.assertIsNone(refusal.next_action_description)
        self.assertEqual(refusal.next_actions, [])

        # Same outcome when explicit_dir=False
        refusal_bare = nonsurveyable_root_refusal(
            verb="attention",
            repo_root=self.real_proj,
            explicit_dir=False,
        )
        self.assertTrue(refusal_bare.may_proceed)
        self.assertIsNone(refusal_bare.human_message)
        self.assertIsNone(refusal_bare.summary)
        self.assertIsNone(refusal_bare.next_action)

    def test_case_b_project_subdirectory_explicit(self):
        """Case (b): Subdirectory of real project with explicit --dir -> refuses honestly.

        Pins:
        - may_proceed is False
        - human text names enclosing root and literal aw <verb> --dir <root>
        - summary matches the shipped inside-project string exactly
        - next_action is None
        - F-14 negatives: no false 'not installed' sentence, no 'aw install .' next action
        - path-freeness: no fixture paths or enclosing root in summary
        """
        refusal = nonsurveyable_root_refusal(
            verb="attention",
            repo_root=self.deep_subdir,
            explicit_dir=True,
        )
        self.assertIsInstance(refusal, RootRefusal)
        self.assertFalse(refusal.may_proceed)
        self.assertFalse(refusal.can_proceed)
        self.assertIsNotNone(refusal.human_message)

        # Human message names enclosing root and gives literal corrected command
        self.assertIn(str(self.real_proj), refusal.human_message)
        self.assertIn(f"aw attention --dir {self.real_proj}", refusal.human_message)
        self.assertIn(
            "explicit --dir is honored verbatim with no upward climb",
            refusal.human_message,
        )

        # Exact shipped summary string
        expected_summary = (
            "the specified directory is inside an AW project but is not its root; "
            "--dir is honored verbatim with no upward climb"
        )
        self.assertEqual(refusal.summary, expected_summary)

        # Next action is None
        self.assertIsNone(refusal.next_action)
        self.assertIsNone(refusal.next_action_command)
        self.assertIsNone(refusal.next_action_description)
        self.assertEqual(refusal.next_actions, [])

        # F-14 Negatives on case (b)
        self.assertNotIn("is not installed in it", refusal.human_message)
        self.assertNotIn("aw install ", refusal.human_message)
        self.assertNotEqual(refusal.next_action_command, "aw install .")

        # Path-freeness of machine summary
        self.assertNotIn(str(self.deep_subdir), refusal.summary)
        self.assertNotIn(str(self.real_proj), refusal.summary)
        self.assertNotIn(str(self.fix_root), refusal.summary)

    def test_case_c_no_project_no_git_explicit(self):
        """Case (c): Directory in NO project and NOT in a git repo with explicit --dir.

        Pins:
        - may_proceed is False
        - summary matches shipped no-project-at-specified-directory string exactly
        - next_action is None
        - path-freeness: no fixture paths in summary
        """
        refusal = nonsurveyable_root_refusal(
            verb="attention",
            repo_root=self.nongit_dir,
            explicit_dir=True,
        )
        self.assertIsInstance(refusal, RootRefusal)
        self.assertFalse(refusal.may_proceed)
        self.assertIsNotNone(refusal.human_message)

        expected_summary = (
            "no AW project found at the specified directory; "
            "--dir is honored verbatim with no upward climb"
        )
        self.assertEqual(refusal.summary, expected_summary)

        self.assertIsNone(refusal.next_action)
        self.assertIsNone(refusal.next_action_command)
        self.assertIsNone(refusal.next_action_description)
        self.assertEqual(refusal.next_actions, [])

        # Path-freeness
        self.assertNotIn(str(self.nongit_dir), refusal.summary)
        self.assertNotIn(str(self.fix_root), refusal.summary)

    def test_case_d_git_repo_without_aw_explicit(self):
        """Case (d): Directory in NO AW project, but INSIDE a git repo with explicit --dir.

        Pins:
        - may_proceed is False
        - summary matches shipped no-project-at-specified-directory string exactly
        - next_action is the literal 'aw install .' with shipped description
        - human text offers aw install <root>
        - path-freeness: no paths in summary or next_action
        """
        refusal = nonsurveyable_root_refusal(
            verb="attention",
            repo_root=self.git_no_aw,
            explicit_dir=True,
        )
        self.assertIsInstance(refusal, RootRefusal)
        self.assertFalse(refusal.may_proceed)
        self.assertIsNotNone(refusal.human_message)
        self.assertIn(
            "IS a git repository, but agent-workflows is not installed in it",
            refusal.human_message,
        )
        self.assertIn(
            f"Install it there with: aw install {self.git_no_aw}", refusal.human_message
        )

        expected_summary = (
            "no AW project found at the specified directory; "
            "--dir is honored verbatim with no upward climb"
        )
        self.assertEqual(refusal.summary, expected_summary)

        # Next action is preserved
        self.assertIsNotNone(refusal.next_action)
        self.assertEqual(refusal.next_action.command, "aw install .")
        self.assertEqual(
            refusal.next_action.description,
            "install agent-workflows in this repo",
        )
        self.assertEqual(refusal.next_action_command, "aw install .")
        self.assertEqual(
            refusal.next_action_description,
            "install agent-workflows in this repo",
        )
        self.assertEqual(len(refusal.next_actions), 1)

        # Path-freeness
        self.assertNotIn(str(self.git_no_aw), refusal.summary)
        self.assertNotIn(str(self.fix_root), refusal.summary)
        self.assertNotIn(str(self.git_no_aw), refusal.next_action.command)
        self.assertNotIn(str(self.git_no_aw), refusal.next_action.description)

    def test_non_explicit_variant_no_project_no_git(self):
        """Non-explicit variant of case (c): bare-cwd climb failed in nongit directory.

        Pins:
        - may_proceed is False
        - summary matches third shipped string ("... at the working directory or any ancestor ...")
        - next_action is None
        - path-freeness: no paths in summary
        """
        refusal = nonsurveyable_root_refusal(
            verb="attention",
            repo_root=self.nongit_dir,
            explicit_dir=False,
        )
        self.assertIsInstance(refusal, RootRefusal)
        self.assertFalse(refusal.may_proceed)
        self.assertIsNotNone(refusal.human_message)

        expected_summary = (
            "no AW project found at the working directory or any ancestor; "
            "cd into the repository or pass --dir <repo>"
        )
        self.assertEqual(refusal.summary, expected_summary)
        self.assertIsNone(refusal.next_action)
        self.assertIsNone(refusal.next_action_command)
        self.assertIsNone(refusal.next_action_description)

        # Path-freeness
        self.assertNotIn(str(self.nongit_dir), refusal.summary)
        self.assertNotIn(str(self.fix_root), refusal.summary)

    def test_non_explicit_variant_git_repo_without_aw(self):
        """Non-explicit variant of case (d): bare-cwd climb failed in git repo without AW.

        Pins:
        - may_proceed is False
        - summary matches third shipped string ("... at the working directory or any ancestor ...")
        - next_action is preserved as 'aw install .' with shipped description
        - path-freeness: no paths in summary or next_action
        """
        refusal = nonsurveyable_root_refusal(
            verb="attention",
            repo_root=self.git_no_aw,
            explicit_dir=False,
        )
        self.assertIsInstance(refusal, RootRefusal)
        self.assertFalse(refusal.may_proceed)
        self.assertIsNotNone(refusal.human_message)

        expected_summary = (
            "no AW project found at the working directory or any ancestor; "
            "cd into the repository or pass --dir <repo>"
        )
        self.assertEqual(refusal.summary, expected_summary)

        self.assertIsNotNone(refusal.next_action)
        self.assertEqual(refusal.next_action.command, "aw install .")
        self.assertEqual(
            refusal.next_action.description,
            "install agent-workflows in this repo",
        )
        self.assertEqual(refusal.next_action_command, "aw install .")
        self.assertEqual(
            refusal.next_action_description,
            "install agent-workflows in this repo",
        )

        # Path-freeness
        self.assertNotIn(str(self.git_no_aw), refusal.summary)
        self.assertNotIn(str(self.fix_root), refusal.summary)
        self.assertNotIn(str(self.git_no_aw), refusal.next_action.command)
        self.assertNotIn(str(self.git_no_aw), refusal.next_action.description)

    def test_purity_and_silence(self):
        """Assert purity: filesystem unchanged before/after, and stdout/stderr empty."""
        snapshot_before = _file_tree_snapshot(self.fix_root)

        stdout_buf = io.StringIO()
        stderr_buf = io.StringIO()

        with contextlib.redirect_stdout(stdout_buf), contextlib.redirect_stderr(
            stderr_buf
        ):
            # Drive calls across all fixture directories and variants
            nonsurveyable_root_refusal("attention", self.real_proj, explicit_dir=True)
            nonsurveyable_root_refusal("attention", self.real_proj, explicit_dir=False)
            nonsurveyable_root_refusal("attention", self.deep_subdir, explicit_dir=True)
            nonsurveyable_root_refusal("attention", self.nongit_dir, explicit_dir=True)
            nonsurveyable_root_refusal("attention", self.nongit_dir, explicit_dir=False)
            nonsurveyable_root_refusal("attention", self.git_no_aw, explicit_dir=True)
            nonsurveyable_root_refusal("attention", self.git_no_aw, explicit_dir=False)

        # Assert complete silence
        self.assertEqual(stdout_buf.getvalue(), "", "stdout must be empty")
        self.assertEqual(stderr_buf.getvalue(), "", "stderr must be empty")

        # Assert purity (filesystem unchanged)
        snapshot_after = _file_tree_snapshot(self.fix_root)
        self.assertEqual(
            snapshot_before, snapshot_after, "filesystem must be unmodified"
        )

    def test_stray_markers_in_temp_root_do_not_poison_children(self):
        """A temp root container with stray markers does not poison child directories.

        Pins:
        (1) The temp root container itself and non-project children report
            find_project_root == None, is_project_dir == False, ProjectLocationCase.NO_PROJECT,
            and CLI exit 2 cannot-run across aw attention and aw specs check.
        (2) A real project child directory with its own .aw/records still resolves normally.
        """
        temp_dir_obj = tempfile.TemporaryDirectory(prefix="awpoll")
        try:
            polluted_tmp = Path(temp_dir_obj.name).resolve()
            (polluted_tmp / ".aw" / "records" / "specs" / "draft").mkdir(parents=True)
            (polluted_tmp / ".agents" / "plans").mkdir(parents=True)
            subprocess.run(
                ["git", "init", str(polluted_tmp)],
                check=True,
                capture_output=True,
            )

            nongit_child = polluted_tmp / "nongit_child"
            nongit_child.mkdir(parents=True)

            git_child = polluted_tmp / "git_child"
            git_child.mkdir(parents=True)
            subprocess.run(
                ["git", "init", str(git_child)],
                check=True,
                capture_output=True,
            )

            real_proj_child = polluted_tmp / "real_proj_child"
            (real_proj_child / ".aw" / "records").mkdir(parents=True)
            child_sub = real_proj_child / "src" / "sub"
            child_sub.mkdir(parents=True)

            with unittest.mock.patch.dict(os.environ, {"TMPDIR": str(polluted_tmp)}):
                # Polluted temp root container itself
                self.assertFalse(is_project_dir(polluted_tmp))
                self.assertIsNone(find_project_root(polluted_tmp))

                # Non-git child inside polluted temp root
                self.assertIsNone(find_project_root(nongit_child))
                self.assertEqual(
                    classify_project_dir(nongit_child).case,
                    ProjectLocationCase.NO_PROJECT,
                )
                self.assertIsNone(git_root_for_message(nongit_child))
                refusal_nongit = nonsurveyable_root_refusal(
                    "attention", nongit_child, explicit_dir=False
                )
                self.assertFalse(refusal_nongit.may_proceed)
                self.assertIsNone(refusal_nongit.next_action)

                # Git child inside polluted temp root
                self.assertIsNone(find_project_root(git_child))
                self.assertEqual(
                    git_root_for_message(git_child),
                    git_child.as_posix(),
                )
                refusal_git = nonsurveyable_root_refusal(
                    "attention", git_child, explicit_dir=False
                )
                self.assertFalse(refusal_git.may_proceed)
                self.assertIsNotNone(refusal_git.next_action)
                self.assertEqual(refusal_git.next_action.command, "aw install .")
                self.assertIn(
                    f"aw install {git_child.as_posix()}", refusal_git.human_message
                )
                self.assertNotIn(
                    f"aw install {polluted_tmp.as_posix()}\n", refusal_git.human_message
                )

                # Real project child inside polluted temp root
                self.assertTrue(is_project_dir(real_proj_child))
                self.assertEqual(find_project_root(child_sub), real_proj_child)

                # Driving CLI subprocesses
                env = os.environ.copy()
                env["TMPDIR"] = str(polluted_tmp)
                for cmd_args in (
                    [
                        sys.executable,
                        "-m",
                        "agent_workflows.cli",
                        "attention",
                        "--agent",
                    ],
                    [
                        sys.executable,
                        "-m",
                        "agent_workflows.cli",
                        "specs",
                        "check",
                        "--agent",
                    ],
                ):
                    res = subprocess.run(
                        cmd_args,
                        cwd=nongit_child,
                        capture_output=True,
                        text=True,
                        env=env,
                    )
                    self.assertEqual(
                        res.returncode,
                        2,
                        f"Expected exit 2 for {cmd_args}, got {res.returncode} with stdout: {res.stdout}",
                    )
                    payload = json.loads(res.stdout)
                    self.assertEqual(
                        payload.get("outcome") or payload.get("status"),
                        "cannot-run",
                    )
        finally:
            temp_dir_obj.cleanup()

    def test_aw_project_ceiling_stops_climb_inside_enclosing_project(self):
        """AW_PROJECT_CEILING stops upward climb from escaping a base directory situated inside a project."""
        custom_base = self.real_proj / "custom_basetemp"
        custom_base.mkdir(parents=True)
        scratch = custom_base / "test_case0"
        scratch.mkdir(parents=True)

        with unittest.mock.patch.dict(
            os.environ, {"AW_PROJECT_CEILING": str(custom_base)}
        ):
            self.assertIsNone(find_project_root(scratch))
            self.assertFalse(is_project_dir(custom_base))
            self.assertEqual(find_project_root(self.deep_subdir), self.real_proj)


class FindProjectRootGitBoundariesAndSubmodulesTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir_obj = tempfile.TemporaryDirectory()
        self.fix_root = Path(self.temp_dir_obj.name).resolve()

    def tearDown(self):
        self.temp_dir_obj.cleanup()

    def test_inner_git_boundary_stops_discovery_under_outer_aw_project(self):
        """Rule 2: An uninstalled nested git repo stops discovery at its own boundary and never binds to outer AW project."""
        outer = self.fix_root / "outer_project"
        outer.mkdir()
        (outer / ".aw" / "records" / "specs" / "draft").mkdir(parents=True)

        inner = outer / "nested_clone"
        inner.mkdir()
        subprocess.run(
            ["git", "init", "-b", "main", str(inner)], check=True, capture_output=True
        )

        inner_sub = inner / "src" / "deep"
        inner_sub.mkdir(parents=True)

        self.assertIsNone(find_project_root(inner), "nested git repo must return None")
        self.assertIsNone(
            find_project_root(inner_sub),
            "subdirectory of nested git repo must return None",
        )

    def test_nongit_aw_project_subdirectories_discover_root(self):
        """Subdirectories of a non-git AW project successfully discover project root."""
        nongit = self.fix_root / "nongit_project"
        nongit.mkdir()
        (nongit / ".aw" / "records" / "specs" / "draft").mkdir(parents=True)

        sub = nongit / "pkg" / "module"
        sub.mkdir(parents=True)

        self.assertEqual(find_project_root(sub), nongit)
        self.assertEqual(find_project_root(nongit), nongit)

    def test_git_submodule_without_aw_resolves_to_parent_with_notice(self):
        """Rule 1: Registered submodule without .aw/ resolves to parent project and prints notice line."""
        parent = self.fix_root / "parent_proj"
        parent.mkdir()
        (parent / ".aw" / "records" / "specs" / "draft").mkdir(parents=True)
        try:
            subprocess.run(
                ["git", "init", "-b", "main", str(parent)],
                check=True,
                capture_output=True,
            )
            subprocess.run(
                ["git", "config", "user.email", "test@example.com"],
                cwd=parent,
                check=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "test"], cwd=parent, check=True
            )
            (parent / "readme.txt").write_text("parent")
            subprocess.run(["git", "add", "readme.txt"], cwd=parent, check=True)
            subprocess.run(
                ["git", "commit", "-m", "parent init"], cwd=parent, check=True
            )

            sub_source = self.fix_root / "sub_source"
            sub_source.mkdir()
            subprocess.run(
                ["git", "init", "-b", "main", str(sub_source)],
                check=True,
                capture_output=True,
            )
            subprocess.run(
                ["git", "config", "user.email", "test@example.com"],
                cwd=sub_source,
                check=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "test"],
                cwd=sub_source,
                check=True,
            )
            (sub_source / "sub.txt").write_text("sub")
            subprocess.run(["git", "add", "sub.txt"], cwd=sub_source, check=True)
            subprocess.run(
                ["git", "commit", "-m", "sub init"], cwd=sub_source, check=True
            )

            subprocess.run(
                [
                    "git",
                    "-c",
                    "protocol.file.allow=always",
                    "submodule",
                    "add",
                    str(sub_source),
                    "sub_no_aw",
                ],
                cwd=parent,
                check=True,
                capture_output=True,
            )
        except (subprocess.SubprocessError, OSError) as exc:
            raise unittest.SkipTest(f"git operations restricted: {exc}")

        sub_no_aw = parent / "sub_no_aw"
        buf = io.StringIO()
        with contextlib.redirect_stderr(buf):
            res = find_project_root(sub_no_aw)
        self.assertEqual(res, parent)
        self.assertIn("notice: parent project was used", buf.getvalue())

        sub_deep = sub_no_aw / "subpkg"
        sub_deep.mkdir()
        buf_deep = io.StringIO()
        with contextlib.redirect_stderr(buf_deep):
            res_deep = find_project_root(sub_deep)
        self.assertEqual(res_deep, parent)
        self.assertIn("notice: parent project was used", buf_deep.getvalue())

    def test_git_submodule_with_own_aw_uses_itself_without_notice(self):
        """Rule 3: Submodule with its own .aw/ uses itself without printing notice."""
        parent = self.fix_root / "parent_proj_3"
        parent.mkdir()
        (parent / ".aw" / "records" / "specs" / "draft").mkdir(parents=True)
        try:
            subprocess.run(
                ["git", "init", "-b", "main", str(parent)],
                check=True,
                capture_output=True,
            )
            subprocess.run(
                ["git", "config", "user.email", "test@example.com"],
                cwd=parent,
                check=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "test"], cwd=parent, check=True
            )
            (parent / "readme.txt").write_text("parent")
            subprocess.run(["git", "add", "readme.txt"], cwd=parent, check=True)
            subprocess.run(
                ["git", "commit", "-m", "parent init"], cwd=parent, check=True
            )

            sub_source_aw = self.fix_root / "sub_source_aw"
            sub_source_aw.mkdir()
            (sub_source_aw / ".aw" / "records" / "specs" / "draft").mkdir(parents=True)
            (
                sub_source_aw / ".aw" / "records" / "specs" / "draft" / "dummy.txt"
            ).write_text("spec")
            subprocess.run(
                ["git", "init", "-b", "main", str(sub_source_aw)],
                check=True,
                capture_output=True,
            )
            subprocess.run(
                ["git", "config", "user.email", "test@example.com"],
                cwd=sub_source_aw,
                check=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "test"],
                cwd=sub_source_aw,
                check=True,
            )
            (sub_source_aw / "sub_aw.txt").write_text("sub_aw")
            subprocess.run(["git", "add", "."], cwd=sub_source_aw, check=True)
            subprocess.run(
                ["git", "commit", "-m", "sub aw init"],
                cwd=sub_source_aw,
                check=True,
            )

            subprocess.run(
                [
                    "git",
                    "-c",
                    "protocol.file.allow=always",
                    "submodule",
                    "add",
                    str(sub_source_aw),
                    "sub_with_aw",
                ],
                cwd=parent,
                check=True,
                capture_output=True,
            )
        except (subprocess.SubprocessError, OSError) as exc:
            raise unittest.SkipTest(f"git operations restricted: {exc}")

        sub_with_aw = parent / "sub_with_aw"
        buf = io.StringIO()
        with contextlib.redirect_stderr(buf):
            res = find_project_root(sub_with_aw)
        self.assertEqual(res, sub_with_aw)
        self.assertEqual("", buf.getvalue())


def test_tmp_path_does_not_climb_past_basetemp(tmp_path: Path):
    """tmp_path fixtures must never resolve to an enclosing AW project or climb past basetemp."""
    assert find_project_root(tmp_path) is None


if __name__ == "__main__":
    unittest.main()
