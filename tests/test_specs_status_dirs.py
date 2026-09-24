"""Integration tests for spec status directory placement across spec writers (IPD r9uvwc)."""

from __future__ import annotations

import argparse
import subprocess
import tempfile
import unittest
from pathlib import Path

from agent_workflows import specs
from agent_workflows import status_set


class SpecStatusDirectoriesTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.temp_dir.name)
        # Initialize git repo
        subprocess.run(
            ["git", "init"], cwd=self.repo_root, check=True, capture_output=True
        )
        subprocess.run(
            ["git", "config", "user.name", "Tester"],
            cwd=self.repo_root,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.email", "tester@example.com"],
            cwd=self.repo_root,
            check=True,
            capture_output=True,
        )
        (self.repo_root / ".aw" / "records" / "specs" / "draft").mkdir(
            parents=True, exist_ok=True
        )
        (self.repo_root / ".aw" / "records" / "specs" / "to-review").mkdir(
            parents=True, exist_ok=True
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_specs_run_new_places_file_in_draft_dir(self) -> None:
        args = argparse.Namespace(
            title="Probe Spec",
            slug="probe-spec",
            summary="A test spec",
            apply=True,
            dir=str(self.repo_root),
            date="2026-09-24",
            agent=False,
            json=False,
            as_agent=False,
        )
        rc = specs.run_new(args)
        self.assertEqual(rc, 0)

        created_files = list(
            (self.repo_root / ".aw" / "records" / "specs").glob("**/*.spec.md")
        )
        self.assertEqual(len(created_files), 1)
        created = created_files[0]
        self.assertEqual(created.parent.name, "draft")
        self.assertIn("- Status: draft", created.read_text(encoding="utf-8"))

    def test_specs_run_set_relocates_file_on_transition(self) -> None:
        spec_path = (
            self.repo_root
            / ".aw"
            / "records"
            / "specs"
            / "draft"
            / "20260924-aa1111-01-aa1111-test.spec.md"
        )
        spec_path.write_text(
            """# Spec: Test Spec

- Date: 2026-09-24
- Status: draft
- Id: aa1111
- Author: tester

## Workflow history

- 2026-09-24 draft (tester): created
""",
            encoding="utf-8",
        )
        subprocess.run(["git", "add", "-A"], cwd=self.repo_root, check=True)
        subprocess.run(
            ["git", "commit", "-m", "initial"], cwd=self.repo_root, check=True
        )

        args = argparse.Namespace(
            path=str(spec_path),
            args=[str(spec_path)],
            status="to-review",
            message="ready for review",
            dir=str(self.repo_root),
            by_human=False,
            allow_open_questions=False,
            commit=True,
            yes=True,
            agent=False,
            json=False,
            as_agent=False,
            no_commit=False,
            date="2026-09-24",
            blocks_release=None,
            priority=None,
            work_kind=None,
            graduated_to=None,
        )
        rc = specs.run_set(args)
        self.assertEqual(rc, 0)

        self.assertFalse(spec_path.exists())
        dest_path = (
            self.repo_root
            / ".aw"
            / "records"
            / "specs"
            / "to-review"
            / "20260924-aa1111-01-aa1111-test.spec.md"
        )
        self.assertTrue(dest_path.exists())
        self.assertIn("- Status: to-review", dest_path.read_text(encoding="utf-8"))

    def test_status_set_run_set_command_relocates_spec(self) -> None:
        spec_path = (
            self.repo_root
            / ".aw"
            / "records"
            / "specs"
            / "draft"
            / "20260924-bb2222-01-bb2222-test.spec.md"
        )
        spec_path.write_text(
            """# Spec: Test Spec

- Date: 2026-09-24
- Status: draft
- Id: bb2222
- Author: tester

## Workflow history

- 2026-09-24 draft (tester): created
""",
            encoding="utf-8",
        )
        subprocess.run(["git", "add", "-A"], cwd=self.repo_root, check=True)
        subprocess.run(
            ["git", "commit", "-m", "initial"], cwd=self.repo_root, check=True
        )

        args = argparse.Namespace(
            args=["to-review", "bb2222"],
            message="ready for review",
            actor="tester",
            dir=str(self.repo_root),
            by_human=False,
            allow_open_questions=False,
            commit=True,
            yes=True,
            agent=False,
            json=False,
            as_agent=False,
            no_commit=False,
            dry_run=False,
            scope_reason=None,
            scope_ack=None,
            status=None,
        )
        rc = status_set.run_set_command(
            ["to-review", "bb2222"],
            scoped_type="specs",
            repo_root=self.repo_root,
            args=args,
        )
        self.assertEqual(rc, 0)

        self.assertFalse(spec_path.exists())
        dest_path = (
            self.repo_root
            / ".aw"
            / "records"
            / "specs"
            / "to-review"
            / "20260924-bb2222-01-bb2222-test.spec.md"
        )
        self.assertTrue(dest_path.exists())
        self.assertIn("- Status: to-review", dest_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
