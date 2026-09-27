"""Integration tests for spec status directory placement across spec writers (IPD r9uvwc, IPD 1bdxcp)."""

from __future__ import annotations

import argparse
import io
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from unittest.mock import patch

from agent_workflows import attention_contract
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

    def test_specs_set_status_dry_run_leaves_file_and_tree_clean(self) -> None:
        from agent_workflows import cli

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

        before_bytes = spec_path.read_bytes()
        dest_path = (
            self.repo_root
            / ".aw"
            / "records"
            / "specs"
            / "to-review"
            / "20260924-aa1111-01-aa1111-test.spec.md"
        )
        sidecar = self.repo_root / ".aw" / "records" / "history.jsonl"

        rc = cli.main(
            [
                "specs",
                "set",
                str(spec_path),
                "--status",
                "to-review",
                "--dry-run",
            ]
        )
        self.assertEqual(rc, 0)
        self.assertTrue(spec_path.exists())
        self.assertEqual(spec_path.read_bytes(), before_bytes)
        self.assertFalse(dest_path.exists())
        res = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=self.repo_root,
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertEqual(res.stdout.strip(), "")
        self.assertFalse(sidecar.exists())

    def test_specs_set_status_approved_dry_run_refuses_without_human_attestation(
        self,
    ) -> None:
        from agent_workflows import cli

        spec_path = (
            self.repo_root
            / ".aw"
            / "records"
            / "specs"
            / "reviewed"
            / "20260924-cc3333-01-cc3333-test.spec.md"
        )
        spec_path.parent.mkdir(parents=True, exist_ok=True)
        spec_path.write_text(
            """# Spec: Test Spec

- Date: 2026-09-24
- Status: reviewed
- Id: cc3333
- Author: tester

## Workflow history

- 2026-09-24 reviewed (tester): ready
- 2026-09-24 draft (tester): created
""",
            encoding="utf-8",
        )
        subprocess.run(["git", "add", "-A"], cwd=self.repo_root, check=True)
        subprocess.run(
            ["git", "commit", "-m", "initial reviewed"],
            cwd=self.repo_root,
            check=True,
        )
        before_bytes = spec_path.read_bytes()

        err = io.StringIO()
        with patch("sys.stdin", io.StringIO()), redirect_stderr(err):
            rc = cli.main(
                [
                    "specs",
                    "set",
                    str(spec_path),
                    "--status",
                    "approved",
                    "--dry-run",
                    "--dir",
                    str(self.repo_root),
                ]
            )
        self.assertEqual(rc, 1)
        self.assertIn("human-only transition", err.getvalue())
        self.assertEqual(spec_path.read_bytes(), before_bytes)

    def test_specs_set_positional_dry_run_leaves_tree_unchanged(self) -> None:
        from agent_workflows import cli

        spec_path = (
            self.repo_root
            / ".aw"
            / "records"
            / "specs"
            / "draft"
            / "20260924-dd4444-01-dd4444-test.spec.md"
        )
        spec_path.write_text(
            """# Spec: Test Spec

- Date: 2026-09-24
- Status: draft
- Id: dd4444
- Author: tester

## Workflow history

- 2026-09-24 draft (tester): created
""",
            encoding="utf-8",
        )
        subprocess.run(["git", "add", "-A"], cwd=self.repo_root, check=True)
        subprocess.run(
            ["git", "commit", "-m", "initial draft"],
            cwd=self.repo_root,
            check=True,
        )
        before_bytes = spec_path.read_bytes()

        rc = cli.main(
            [
                "specs",
                "set",
                "to-review",
                "dd4444",
                "--dry-run",
                "--dir",
                str(self.repo_root),
            ]
        )
        self.assertEqual(rc, 0)
        self.assertTrue(spec_path.exists())
        self.assertEqual(spec_path.read_bytes(), before_bytes)
        res = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=self.repo_root,
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertEqual(res.stdout.strip(), "")


class LiveSpecsTreeInvariantTests(unittest.TestCase):
    """Verify invariants over the live repository specs tree."""

    def test_every_spec_directory_agrees_with_its_status(self) -> None:
        repo_root = Path(__file__).resolve().parent.parent
        specs_dir = repo_root / ".aw" / "records" / "specs"
        spec_files = list(specs_dir.rglob("*.spec.md"))
        self.assertGreaterEqual(
            len(spec_files), 28, "Live specs tree must have at least 28 specs"
        )

        for p in spec_files:
            text = p.read_text(encoding="utf-8")
            status = specs._read_status(specs._lines(text))
            self.assertIsNotNone(status, f"Spec {p.name} must have a status bullet")
            self.assertIn(
                status,
                attention_contract.SPEC_STATUSES,
                f"Spec {p.name} status {status} must be recognized",
            )
            self.assertEqual(
                p.parent.name,
                status,
                f"Spec {p.name} in dir {p.parent.name} must agree with status {status}",
            )

    def test_specs_readme_documents_layout_and_has_no_en_or_em_dashes(self) -> None:
        repo_root = Path(__file__).resolve().parent.parent
        readme_path = repo_root / ".aw" / "records" / "specs" / "README.md"
        self.assertTrue(readme_path.exists(), "Specs README.md must exist")
        content = readme_path.read_text(encoding="utf-8")
        self.assertNotIn("—", content, "README must not contain em dash")
        self.assertNotIn("–", content, "README must not contain en dash")
        for status in attention_contract.SPEC_STATUSES:
            self.assertIn(
                f"`{status}/`",
                content,
                f"README must document status directory `{status}/`",
            )


if __name__ == "__main__":
    unittest.main()
