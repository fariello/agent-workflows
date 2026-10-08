"""Outcome tests for history sidecar write ordering (IPD ulepef E-06).

Ensures that the advisory history sidecar event is recorded only AFTER the durable
write succeeds, so a failed durable write leaves no phantom event in the sidecar log.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import pytest

from agent_workflows import cli


def _skip_if_root() -> None:
    if hasattr(os, "geteuid") and os.geteuid() == 0:
        pytest.skip("Running as root; chmod does not deny write")


class HistoryWriteOrderTests(unittest.TestCase):
    """Verify write ordering across backlog set, backlog note, specs set, specs note."""

    def setUp(self) -> None:
        self.tmp = tempfile.mkdtemp()
        self.repo = Path(self.tmp)
        subprocess.run(
            ["git", "init", "-b", "main"],
            cwd=self.repo,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Tester"],
            cwd=self.repo,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.email", "tester@example.com"],
            cwd=self.repo,
            check=True,
            capture_output=True,
        )
        self.sidecar = self.repo / ".aw" / "records" / "history.jsonl"
        self._restorations: list[tuple[Path, int]] = []

    def tearDown(self) -> None:
        for path, mode in reversed(self._restorations):
            try:
                if path.exists():
                    path.chmod(mode)
            except OSError:
                pass
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _set_mode_with_cleanup(self, path: Path, mode: int) -> None:
        old_mode = path.stat().st_mode & 0o777
        self._restorations.append((path, old_mode))
        path.chmod(mode)

    # ----------------------------------------------------------------------------------
    # backlog set
    # ----------------------------------------------------------------------------------

    def test_backlog_set_failed_write_leaves_no_sidecar_and_artifact_unchanged(
        self,
    ) -> None:
        _skip_if_root()
        open_dir = self.repo / ".aw" / "records" / "backlog" / "open"
        parked_dir = self.repo / ".aw" / "records" / "backlog" / "parked"
        open_dir.mkdir(parents=True)
        parked_dir.mkdir(parents=True)

        item = open_dir / "20261001-demo01-01-bk0001-open-item.backlog.md"
        item.write_text(
            "- Id: bk0001\n"
            "- Status: open\n"
            "- Priority: medium\n"
            "- Work-Kind: feature\n"
            "- Set: demo01\n"
            "- Summary: test open item\n\n"
            "## Workflow history\n"
            "- 2026-10-01 created (tester): initial\n",
            encoding="utf-8",
        )
        subprocess.run(
            ["git", "add", "-A"], cwd=self.repo, check=True, capture_output=True
        )
        subprocess.run(
            ["git", "commit", "-m", "init", "--no-verify"],
            cwd=self.repo,
            check=True,
            capture_output=True,
        )

        before_bytes = item.read_bytes()
        self._set_mode_with_cleanup(parked_dir, 0o500)

        with pytest.raises(OSError):
            cli.main(
                [
                    "backlog",
                    "set",
                    str(item),
                    "--status",
                    "parked",
                    "--dir",
                    str(self.repo),
                    "--no-commit",
                ]
            )

        self.assertFalse(self.sidecar.exists())
        self.assertTrue(item.exists())
        self.assertEqual(item.read_bytes(), before_bytes)

    def test_backlog_set_successful_write_records_sidecar_event(self) -> None:
        open_dir = self.repo / ".aw" / "records" / "backlog" / "open"
        parked_dir = self.repo / ".aw" / "records" / "backlog" / "parked"
        open_dir.mkdir(parents=True)
        parked_dir.mkdir(parents=True)

        item = open_dir / "20261001-demo01-01-bk0001-open-item.backlog.md"
        item.write_text(
            "- Id: bk0001\n"
            "- Status: open\n"
            "- Priority: medium\n"
            "- Work-Kind: feature\n"
            "- Set: demo01\n"
            "- Summary: test open item\n\n"
            "## Workflow history\n"
            "- 2026-10-01 created (tester): initial\n",
            encoding="utf-8",
        )
        subprocess.run(
            ["git", "add", "-A"], cwd=self.repo, check=True, capture_output=True
        )
        subprocess.run(
            ["git", "commit", "-m", "init", "--no-verify"],
            cwd=self.repo,
            check=True,
            capture_output=True,
        )

        rc = cli.main(
            [
                "backlog",
                "set",
                str(item),
                "--status",
                "parked",
                "--dir",
                str(self.repo),
                "--no-commit",
            ]
        )
        self.assertEqual(rc, 0)
        dest_item = parked_dir / "20261001-demo01-01-bk0001-open-item.backlog.md"
        self.assertTrue(dest_item.exists())
        self.assertFalse(item.exists())

        self.assertTrue(self.sidecar.exists())
        lines = [
            line.strip()
            for line in self.sidecar.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        self.assertEqual(len(lines), 1)
        record = json.loads(lines[0])
        self.assertEqual(record["id6"], "bk0001")
        self.assertEqual(record["tree"], "backlog")
        self.assertEqual(record["workflow"], "aw backlog set")
        self.assertEqual(record["message"], "status -> parked")

    # ----------------------------------------------------------------------------------
    # backlog note
    # ----------------------------------------------------------------------------------

    def test_backlog_note_failed_write_leaves_no_sidecar_and_artifact_unchanged(
        self,
    ) -> None:
        _skip_if_root()
        open_dir = self.repo / ".aw" / "records" / "backlog" / "open"
        open_dir.mkdir(parents=True)

        item = open_dir / "20261001-demo01-01-bk0002-open-item.backlog.md"
        item.write_text(
            "- Id: bk0002\n"
            "- Status: open\n"
            "- Priority: medium\n"
            "- Work-Kind: feature\n"
            "- Set: demo01\n"
            "- Summary: test note item\n\n"
            "## Workflow history\n"
            "- 2026-10-01 created (tester): initial\n",
            encoding="utf-8",
        )
        subprocess.run(
            ["git", "add", "-A"], cwd=self.repo, check=True, capture_output=True
        )
        subprocess.run(
            ["git", "commit", "-m", "init", "--no-verify"],
            cwd=self.repo,
            check=True,
            capture_output=True,
        )

        before_bytes = item.read_bytes()
        self._set_mode_with_cleanup(open_dir, 0o500)

        with pytest.raises(OSError):
            cli.main(
                [
                    "backlog",
                    "note",
                    str(item),
                    "--message",
                    "first note",
                    "--dir",
                    str(self.repo),
                ]
            )

        self.assertFalse(self.sidecar.exists())
        self.assertTrue(item.exists())
        self.assertEqual(item.read_bytes(), before_bytes)

    def test_backlog_note_successful_write_records_sidecar_event(self) -> None:
        open_dir = self.repo / ".aw" / "records" / "backlog" / "open"
        open_dir.mkdir(parents=True)

        item = open_dir / "20261001-demo01-01-bk0002-open-item.backlog.md"
        item.write_text(
            "- Id: bk0002\n"
            "- Status: open\n"
            "- Priority: medium\n"
            "- Work-Kind: feature\n"
            "- Set: demo01\n"
            "- Summary: test note item\n\n"
            "## Workflow history\n"
            "- 2026-10-01 created (tester): initial\n",
            encoding="utf-8",
        )
        subprocess.run(
            ["git", "add", "-A"], cwd=self.repo, check=True, capture_output=True
        )
        subprocess.run(
            ["git", "commit", "-m", "init", "--no-verify"],
            cwd=self.repo,
            check=True,
            capture_output=True,
        )

        rc = cli.main(
            [
                "backlog",
                "note",
                str(item),
                "--message",
                "first note",
                "--dir",
                str(self.repo),
            ]
        )
        self.assertEqual(rc, 0)
        self.assertIn("first note", item.read_text(encoding="utf-8"))

        self.assertTrue(self.sidecar.exists())
        lines = [
            line.strip()
            for line in self.sidecar.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        self.assertEqual(len(lines), 1)
        record = json.loads(lines[0])
        self.assertEqual(record["id6"], "bk0002")
        self.assertEqual(record["tree"], "backlog")
        self.assertEqual(record["workflow"], "aw backlog note")
        self.assertEqual(record["message"], "note: first note")

    # ----------------------------------------------------------------------------------
    # specs set (directory-crossing)
    # ----------------------------------------------------------------------------------

    def test_specs_set_failed_write_leaves_no_sidecar_and_artifact_unchanged(
        self,
    ) -> None:
        _skip_if_root()
        draft_dir = self.repo / ".aw" / "records" / "specs" / "draft"
        to_review_dir = self.repo / ".aw" / "records" / "specs" / "to-review"
        draft_dir.mkdir(parents=True)
        to_review_dir.mkdir(parents=True)

        spec = draft_dir / "20261001-sp0001-01-sp0001-spec.spec.md"
        spec.write_text(
            "# Spec: Spec One\n\n"
            "- Date: 2026-10-01\n"
            "- Status: draft\n"
            "- Id: sp0001\n"
            "- Author: tester\n\n"
            "## Workflow history\n"
            "- 2026-10-01 draft (tester): initial\n",
            encoding="utf-8",
        )
        subprocess.run(
            ["git", "add", "-A"], cwd=self.repo, check=True, capture_output=True
        )
        subprocess.run(
            ["git", "commit", "-m", "init", "--no-verify"],
            cwd=self.repo,
            check=True,
            capture_output=True,
        )

        before_bytes = spec.read_bytes()
        self._set_mode_with_cleanup(to_review_dir, 0o500)

        with pytest.raises(OSError):
            cli.main(
                [
                    "specs",
                    "set",
                    str(spec),
                    "--status",
                    "to-review",
                    "--dir",
                    str(self.repo),
                    "--no-commit",
                ]
            )

        self.assertFalse(self.sidecar.exists())
        self.assertTrue(spec.exists())
        self.assertEqual(spec.read_bytes(), before_bytes)
        self.assertEqual(list(to_review_dir.iterdir()), [])

    def test_specs_set_successful_write_records_sidecar_event(self) -> None:
        draft_dir = self.repo / ".aw" / "records" / "specs" / "draft"
        to_review_dir = self.repo / ".aw" / "records" / "specs" / "to-review"
        draft_dir.mkdir(parents=True)
        to_review_dir.mkdir(parents=True)

        spec = draft_dir / "20261001-sp0001-01-sp0001-spec.spec.md"
        spec.write_text(
            "# Spec: Spec One\n\n"
            "- Date: 2026-10-01\n"
            "- Status: draft\n"
            "- Id: sp0001\n"
            "- Author: tester\n\n"
            "## Workflow history\n"
            "- 2026-10-01 draft (tester): initial\n",
            encoding="utf-8",
        )
        subprocess.run(
            ["git", "add", "-A"], cwd=self.repo, check=True, capture_output=True
        )
        subprocess.run(
            ["git", "commit", "-m", "init", "--no-verify"],
            cwd=self.repo,
            check=True,
            capture_output=True,
        )

        rc = cli.main(
            [
                "specs",
                "set",
                str(spec),
                "--status",
                "to-review",
                "--message",
                "ready for review",
                "--dir",
                str(self.repo),
                "--no-commit",
            ]
        )
        self.assertEqual(rc, 0)
        dest_spec = to_review_dir / "20261001-sp0001-01-sp0001-spec.spec.md"
        self.assertTrue(dest_spec.exists())
        self.assertFalse(spec.exists())

        self.assertTrue(self.sidecar.exists())
        lines = [
            line.strip()
            for line in self.sidecar.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        self.assertEqual(len(lines), 1)
        record = json.loads(lines[0])
        self.assertEqual(record["id6"], "sp0001")
        self.assertEqual(record["tree"], "specs")
        self.assertEqual(record["workflow"], "aw specs")
        self.assertEqual(record["message"], "to-review: ready for review")

    # ----------------------------------------------------------------------------------
    # specs note (no --dir passed)
    # ----------------------------------------------------------------------------------

    def test_specs_note_failed_write_leaves_no_sidecar_and_artifact_unchanged(
        self,
    ) -> None:
        _skip_if_root()
        draft_dir = self.repo / ".aw" / "records" / "specs" / "draft"
        draft_dir.mkdir(parents=True)

        spec = draft_dir / "20261001-sp0002-01-sp0002-spec.spec.md"
        spec.write_text(
            "# Spec: Spec Two\n\n"
            "- Date: 2026-10-01\n"
            "- Status: draft\n"
            "- Id: sp0002\n"
            "- Author: tester\n\n"
            "## Workflow history\n"
            "- 2026-10-01 draft (tester): initial\n",
            encoding="utf-8",
        )
        subprocess.run(
            ["git", "add", "-A"], cwd=self.repo, check=True, capture_output=True
        )
        subprocess.run(
            ["git", "commit", "-m", "init", "--no-verify"],
            cwd=self.repo,
            check=True,
            capture_output=True,
        )

        before_bytes = spec.read_bytes()
        self._set_mode_with_cleanup(draft_dir, 0o500)

        with pytest.raises(OSError):
            cli.main(
                [
                    "specs",
                    "note",
                    str(spec),
                    "--message",
                    "a test spec note",
                ]
            )

        self.assertFalse(self.sidecar.exists())
        self.assertTrue(spec.exists())
        self.assertEqual(spec.read_bytes(), before_bytes)

    def test_specs_note_successful_write_records_sidecar_event(self) -> None:
        draft_dir = self.repo / ".aw" / "records" / "specs" / "draft"
        draft_dir.mkdir(parents=True)

        spec = draft_dir / "20261001-sp0002-01-sp0002-spec.spec.md"
        spec.write_text(
            "# Spec: Spec Two\n\n"
            "- Date: 2026-10-01\n"
            "- Status: draft\n"
            "- Id: sp0002\n"
            "- Author: tester\n\n"
            "## Workflow history\n"
            "- 2026-10-01 draft (tester): initial\n",
            encoding="utf-8",
        )
        subprocess.run(
            ["git", "add", "-A"], cwd=self.repo, check=True, capture_output=True
        )
        subprocess.run(
            ["git", "commit", "-m", "init", "--no-verify"],
            cwd=self.repo,
            check=True,
            capture_output=True,
        )

        rc = cli.main(
            [
                "specs",
                "note",
                str(spec),
                "--message",
                "a test spec note",
            ]
        )
        self.assertEqual(rc, 0)
        self.assertIn("a test spec note", spec.read_text(encoding="utf-8"))

        self.assertTrue(self.sidecar.exists())
        lines = [
            line.strip()
            for line in self.sidecar.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        self.assertEqual(len(lines), 1)
        record = json.loads(lines[0])
        self.assertEqual(record["id6"], "sp0002")
        self.assertEqual(record["tree"], "specs")
        self.assertEqual(record["workflow"], "aw specs")
        self.assertEqual(record["message"], "note: a test spec note")
