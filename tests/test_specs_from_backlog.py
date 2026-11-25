"""Integration tests for aw specs set --from-backlog across both spellings (IPD uruqaz)."""

from __future__ import annotations

import argparse
import subprocess
import tempfile
import unittest
from pathlib import Path

from agent_workflows import specs, status_set
from tests.record_builder import RecordBuilder, assert_field


class SpecsFromBacklogTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.temp_dir.name)
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
        (self.repo_root / ".aw" / "records" / "releases").mkdir(
            parents=True, exist_ok=True
        )
        (self.repo_root / ".aw" / "records" / "backlog" / "open").mkdir(
            parents=True, exist_ok=True
        )

        # Planned release relaaa
        (
            self.repo_root
            / ".aw"
            / "records"
            / "releases"
            / "20260925-relaaa-01-relaaa-test-rel.release.md"
        ).write_text(
            RecordBuilder().release(
                id6="relaaa",
                version="1.0.0",
                status="planned",
                summary="Test Release",
                when="2026-09-25",
                author="tester",
                history=["- 2026-09-25 planned (tester): planned"],
                text_only=True,
            ),
            encoding="utf-8",
        )
        # Planned release relbbb
        (
            self.repo_root
            / ".aw"
            / "records"
            / "releases"
            / "20260925-relbbb-01-relbbb-other-rel.release.md"
        ).write_text(
            RecordBuilder().release(
                id6="relbbb",
                version="2.0.0",
                status="planned",
                summary="Other Release",
                when="2026-09-25",
                author="tester",
                history=["- 2026-09-25 planned (tester): planned"],
                text_only=True,
            ),
            encoding="utf-8",
        )
        # Open backlog item with Blocks-Release: relaaa
        (
            self.repo_root
            / ".aw"
            / "records"
            / "backlog"
            / "open"
            / "20260925-bkl001-01-bkl001-my-bug.backlog.md"
        ).write_text(
            RecordBuilder().backlog(
                id6="bkl001",
                status="open",
                priority="medium",
                work_kind="bug",
                blocks_release="relaaa",
                summary="Test bug",
                when="2026-09-25",
                author="tester",
                history=["- 2026-09-25 open (tester): created"],
                text_only=True,
            ),
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _create_spec(
        self,
        id6: str,
        name: str,
        blocks_release: str | None = None,
        from_backlog: str | None = None,
    ) -> Path:
        p = (
            self.repo_root
            / ".aw"
            / "records"
            / "specs"
            / "draft"
            / f"20260925-{id6}-01-{id6}-{name}.spec.md"
        )
        extra: dict[str, str] = {}
        if blocks_release is not None:
            extra["blocks_release"] = blocks_release
        if from_backlog is not None:
            extra["from_backlog"] = from_backlog
        content = RecordBuilder().spec(
            id6=id6,
            title=name,
            when="2026-09-25",
            status="draft",
            author="tester",
            history=["- 2026-09-25 draft (tester): created"],
            body="",
            text_only=True,
            **extra,
        )
        p.write_text(content, encoding="utf-8")
        subprocess.run(["git", "add", "-A"], cwd=self.repo_root, check=True)
        subprocess.run(
            ["git", "commit", "-m", f"add spec {id6}"],
            cwd=self.repo_root,
            check=True,
            capture_output=True,
        )
        return p

    # --- --status spelling tests (specs.run_set) ---

    def test_status_spelling_from_backlog_writes_field_and_inherits_gate(self) -> None:
        spec_path = self._create_spec("sp0001", "spec-a")
        args = argparse.Namespace(
            path=str(spec_path),
            args=[str(spec_path)],
            status="to-review",
            message="ready for review",
            dir=str(self.repo_root),
            by_human=False,
            allow_open_questions=False,
            commit=False,
            yes=True,
            agent=False,
            json=False,
            as_agent=False,
            no_commit=True,
            date="2026-09-25",
            blocks_release=None,
            priority=None,
            work_kind=None,
            graduated_to=None,
            from_backlog="bkl001",
        )
        rc = specs.run_set(args)
        self.assertEqual(rc, 0)

        dest_path = (
            self.repo_root
            / ".aw"
            / "records"
            / "specs"
            / "to-review"
            / "20260925-sp0001-01-sp0001-spec-a.spec.md"
        )
        self.assertTrue(dest_path.exists())
        assert_field(dest_path, "status", "to-review")
        assert_field(dest_path, "from_backlog", "bkl001")
        assert_field(dest_path, "blocks_release", "relaaa")

    def test_status_spelling_explicit_blocks_release_wins(self) -> None:
        spec_path = self._create_spec("sp0002", "spec-b")
        args = argparse.Namespace(
            path=str(spec_path),
            args=[str(spec_path)],
            status="to-review",
            message="ready for review",
            dir=str(self.repo_root),
            by_human=False,
            allow_open_questions=False,
            commit=False,
            yes=True,
            agent=False,
            json=False,
            as_agent=False,
            no_commit=True,
            date="2026-09-25",
            blocks_release="relbbb",
            priority=None,
            work_kind=None,
            graduated_to=None,
            from_backlog="bkl001",
        )
        rc = specs.run_set(args)
        self.assertEqual(rc, 0)

        dest_path = (
            self.repo_root
            / ".aw"
            / "records"
            / "specs"
            / "to-review"
            / "20260925-sp0002-01-sp0002-spec-b.spec.md"
        )
        self.assertTrue(dest_path.exists())
        assert_field(dest_path, "status", "to-review")
        assert_field(dest_path, "from_backlog", "bkl001")
        assert_field(dest_path, "blocks_release", "relbbb")

    def test_status_spelling_existing_gate_not_overwritten(self) -> None:
        spec_path = self._create_spec("sp0003", "spec-c", blocks_release="relbbb")
        args = argparse.Namespace(
            path=str(spec_path),
            args=[str(spec_path)],
            status="to-review",
            message="ready for review",
            dir=str(self.repo_root),
            by_human=False,
            allow_open_questions=False,
            commit=False,
            yes=True,
            agent=False,
            json=False,
            as_agent=False,
            no_commit=True,
            date="2026-09-25",
            blocks_release=None,
            priority=None,
            work_kind=None,
            graduated_to=None,
            from_backlog="bkl001",
        )
        rc = specs.run_set(args)
        self.assertEqual(rc, 0)

        dest_path = (
            self.repo_root
            / ".aw"
            / "records"
            / "specs"
            / "to-review"
            / "20260925-sp0003-01-sp0003-spec-c.spec.md"
        )
        self.assertTrue(dest_path.exists())
        assert_field(dest_path, "status", "to-review")
        assert_field(dest_path, "from_backlog", "bkl001")
        assert_field(dest_path, "blocks_release", "relbbb")

    def test_status_spelling_from_backlog_dash_clears_field_and_inherits_nothing(
        self,
    ) -> None:
        spec_path = self._create_spec("sp0004", "spec-d", from_backlog="bkl001")
        args = argparse.Namespace(
            path=str(spec_path),
            args=[str(spec_path)],
            status="to-review",
            message="ready for review",
            dir=str(self.repo_root),
            by_human=False,
            allow_open_questions=False,
            commit=False,
            yes=True,
            agent=False,
            json=False,
            as_agent=False,
            no_commit=True,
            date="2026-09-25",
            blocks_release=None,
            priority=None,
            work_kind=None,
            graduated_to=None,
            from_backlog="-",
        )
        rc = specs.run_set(args)
        self.assertEqual(rc, 0)

        dest_path = (
            self.repo_root
            / ".aw"
            / "records"
            / "specs"
            / "to-review"
            / "20260925-sp0004-01-sp0004-spec-d.spec.md"
        )
        self.assertTrue(dest_path.exists())
        content = dest_path.read_text(encoding="utf-8")
        assert_field(dest_path, "status", "to-review")
        self.assertNotIn("From-Backlog", content)
        self.assertNotIn("Blocks-Release", content)

    # --- bare spelling tests (status_set.run_set_command) ---

    def test_bare_spelling_from_backlog_writes_field_and_inherits_gate(self) -> None:
        self._create_spec("sp0005", "spec-e")
        args = argparse.Namespace(
            args=["to-review", "sp0005"],
            message="ready for review",
            actor="tester",
            dir=str(self.repo_root),
            by_human=False,
            allow_open_questions=False,
            commit=False,
            yes=True,
            agent=False,
            json=False,
            as_agent=False,
            no_commit=True,
            dry_run=False,
            scope_reason=None,
            scope_ack=None,
            status=None,
            from_backlog="bkl001",
            blocks_release=None,
        )
        rc = status_set.run_set_command(
            ["to-review", "sp0005"],
            scoped_type="specs",
            repo_root=self.repo_root,
            args=args,
        )
        self.assertEqual(rc, 0)

        dest_path = (
            self.repo_root
            / ".aw"
            / "records"
            / "specs"
            / "to-review"
            / "20260925-sp0005-01-sp0005-spec-e.spec.md"
        )
        self.assertTrue(dest_path.exists())
        assert_field(dest_path, "status", "to-review")
        assert_field(dest_path, "from_backlog", "bkl001")
        assert_field(dest_path, "blocks_release", "relaaa")

    def test_bare_spelling_explicit_blocks_release_wins(self) -> None:
        self._create_spec("sp0006", "spec-f")
        args = argparse.Namespace(
            args=["to-review", "sp0006"],
            message="ready for review",
            actor="tester",
            dir=str(self.repo_root),
            by_human=False,
            allow_open_questions=False,
            commit=False,
            yes=True,
            agent=False,
            json=False,
            as_agent=False,
            no_commit=True,
            dry_run=False,
            scope_reason=None,
            scope_ack=None,
            status=None,
            from_backlog="bkl001",
            blocks_release="relbbb",
        )
        rc = status_set.run_set_command(
            ["to-review", "sp0006"],
            scoped_type="specs",
            repo_root=self.repo_root,
            args=args,
        )
        self.assertEqual(rc, 0)

        dest_path = (
            self.repo_root
            / ".aw"
            / "records"
            / "specs"
            / "to-review"
            / "20260925-sp0006-01-sp0006-spec-f.spec.md"
        )
        self.assertTrue(dest_path.exists())
        assert_field(dest_path, "status", "to-review")
        assert_field(dest_path, "from_backlog", "bkl001")
        assert_field(dest_path, "blocks_release", "relbbb")

    def test_bare_spelling_existing_gate_not_overwritten(self) -> None:
        self._create_spec("sp0007", "spec-g", blocks_release="relbbb")
        args = argparse.Namespace(
            args=["to-review", "sp0007"],
            message="ready for review",
            actor="tester",
            dir=str(self.repo_root),
            by_human=False,
            allow_open_questions=False,
            commit=False,
            yes=True,
            agent=False,
            json=False,
            as_agent=False,
            no_commit=True,
            dry_run=False,
            scope_reason=None,
            scope_ack=None,
            status=None,
            from_backlog="bkl001",
            blocks_release=None,
        )
        rc = status_set.run_set_command(
            ["to-review", "sp0007"],
            scoped_type="specs",
            repo_root=self.repo_root,
            args=args,
        )
        self.assertEqual(rc, 0)

        dest_path = (
            self.repo_root
            / ".aw"
            / "records"
            / "specs"
            / "to-review"
            / "20260925-sp0007-01-sp0007-spec-g.spec.md"
        )
        self.assertTrue(dest_path.exists())
        assert_field(dest_path, "status", "to-review")
        assert_field(dest_path, "from_backlog", "bkl001")
        assert_field(dest_path, "blocks_release", "relbbb")

    def test_bare_spelling_from_backlog_dash_clears_field_and_inherits_nothing(
        self,
    ) -> None:
        self._create_spec("sp0008", "spec-h", from_backlog="bkl001")
        args = argparse.Namespace(
            args=["to-review", "sp0008"],
            message="ready for review",
            actor="tester",
            dir=str(self.repo_root),
            by_human=False,
            allow_open_questions=False,
            commit=False,
            yes=True,
            agent=False,
            json=False,
            as_agent=False,
            no_commit=True,
            dry_run=False,
            scope_reason=None,
            scope_ack=None,
            status=None,
            from_backlog="-",
            blocks_release=None,
        )
        rc = status_set.run_set_command(
            ["to-review", "sp0008"],
            scoped_type="specs",
            repo_root=self.repo_root,
            args=args,
        )
        self.assertEqual(rc, 0)

        dest_path = (
            self.repo_root
            / ".aw"
            / "records"
            / "specs"
            / "to-review"
            / "20260925-sp0008-01-sp0008-spec-h.spec.md"
        )
        self.assertTrue(dest_path.exists())
        content = dest_path.read_text(encoding="utf-8")
        assert_field(dest_path, "status", "to-review")
        self.assertNotIn("From-Backlog", content)
        self.assertNotIn("Blocks-Release", content)
