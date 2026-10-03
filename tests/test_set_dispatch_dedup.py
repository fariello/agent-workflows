"""Outcome tests for deduplicated set dispatch helpers (IPD c6f6sj).

Covers:
1. Self-commit deduplication across both spellings (`aw specs set <path> --status <s> --commit`
   and `aw specs set --dir <root> <s> <id6> --commit`):
   (a) --status spelling produces exactly chore(specs): set status <s> with single-rename content.
   (b) positional spelling produces the same commit message and single-rename content.
   (c) unrelated staged file is not folded into the commit and survives staged.
   (d) --no-commit commits nothing on both spellings.
   (e) --yes without --commit in agent mode commits nothing on both spellings.

2. From-Backlog gate inheritance across both spellings:
   (a) --status spelling inherits gate and prints 'aw specs set:' notice prefix.
   (b) positional spelling inherits gate and prints 'aw set:' notice prefix.
   (c) explicit --blocks-release wins over inheritance on both spellings.
   (d) existing - Blocks-Release: on artifact is preserved on both spellings.
   (e) resolvable ungated backlog item exits 0, writes From-Backlog, and writes no gate.

Tests outcomes and behavior only; does not inspect source code structure.
"""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from tests.support import run_cli


def _setup_test_repo(root: Path, *, with_gate: bool = True) -> dict[str, Path]:
    """Create a minimal committed repository with spec, backlog, and release records."""
    subprocess.run(
        ["git", "init", "-b", "main"], cwd=root, check=True, capture_output=True
    )
    subprocess.run(
        ["git", "config", "user.name", "Tester"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "tester@example.com"],
        cwd=root,
        check=True,
        capture_output=True,
    )

    paths: dict[str, Path] = {}

    # Release relaaa
    rel_dir = root / ".aw" / "records" / "releases"
    rel_dir.mkdir(parents=True, exist_ok=True)
    rel_path = rel_dir / "20260930-relaaa-01-relaaa-test-rel.release.md"
    rel_path.write_text(
        "# Release: Test Release\n\n"
        "- Id: relaaa\n"
        "- Status: planned\n"
        "- Version: 1.0.0\n"
        "- Summary: Test Release\n\n"
        "## Workflow history\n"
        "- 2026-09-30 planned (tester): created\n",
        encoding="utf-8",
    )
    paths["release"] = rel_path

    # Backlog item with gate
    bk_dir = root / ".aw" / "records" / "backlog" / "open"
    bk_dir.mkdir(parents=True, exist_ok=True)
    bk_path = bk_dir / "20260930-bkl001-01-bkl001-test-bug.backlog.md"
    bk_path.write_text(
        "- Id: bkl001\n"
        "- Status: open\n"
        "- Priority: medium\n"
        "- Work-Kind: bug\n"
        + ("- Blocks-Release: relaaa\n" if with_gate else "")
        + "- Summary: Test bug\n\n"
        "## Workflow history\n"
        "- 2026-09-30 open (tester): created\n",
        encoding="utf-8",
    )
    paths["backlog"] = bk_path

    # Backlog item without gate (resolvable ungated item)
    bk_ungated_path = bk_dir / "20260930-bklung-01-bklung-ungated-item.backlog.md"
    bk_ungated_path.write_text(
        "- Id: bklung\n"
        "- Status: open\n"
        "- Priority: medium\n"
        "- Work-Kind: chore\n"
        "- Summary: Ungated task\n\n"
        "## Workflow history\n"
        "- 2026-09-30 open (tester): created\n",
        encoding="utf-8",
    )
    paths["backlog_ungated"] = bk_ungated_path

    # Spec (ungated, draft)
    spec_dir = root / ".aw" / "records" / "specs" / "draft"
    spec_dir.mkdir(parents=True, exist_ok=True)
    spec_path = spec_dir / "20260930-spc001-01-spc001-test-spec.spec.md"
    spec_path.write_text(
        "# Spec: Test Spec\n\n"
        "- Date: 2026-09-30\n"
        "- Status: draft\n"
        "- Id: spc001\n\n"
        "## Workflow history\n"
        "- 2026-09-30 draft (tester): created\n",
        encoding="utf-8",
    )
    paths["spec"] = spec_path

    # Spec (already carrying an existing gate)
    spec_gtd_path = spec_dir / "20260930-spcgtd-01-spcgtd-gated-spec.spec.md"
    spec_gtd_path.write_text(
        "# Spec: Gated Spec\n\n"
        "- Date: 2026-09-30\n"
        "- Status: draft\n"
        "- Blocks-Release: relorig\n"
        "- Id: spcgtd\n\n"
        "## Workflow history\n"
        "- 2026-09-30 draft (tester): created\n",
        encoding="utf-8",
    )
    paths["spec_gated"] = spec_gtd_path

    subprocess.run(["git", "add", "-A"], cwd=root, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "init repo"], cwd=root, check=True, capture_output=True
    )
    return paths


class TestSelfCommitDedup(unittest.TestCase):
    """E-03: Self-commit outcome tests across both dispatch spellings."""

    def test_self_commit_specs_set_status_creates_single_rename_commit(self) -> None:
        """(a) aw specs set <path> --status <s> --commit produces chore(specs) commit with single rename."""
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            paths = _setup_test_repo(repo_root)
            spec_path = paths["spec"]

            proc = run_cli(
                "specs",
                "set",
                str(spec_path),
                "--status",
                "to-review",
                "--message",
                "move to to-review",
                "--commit",
                "--yes",
                cwd=repo_root,
            )
            self.assertEqual(
                proc.returncode, 0, f"stdout: {proc.stdout}\nstderr: {proc.stderr}"
            )

            # Check commit message
            msg = subprocess.run(
                ["git", "log", "-1", "--format=%s"],
                cwd=repo_root,
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip()
            self.assertEqual(msg, "chore(specs): set status to-review")

            # Check commit content is single rename
            status_out = (
                subprocess.run(
                    ["git", "show", "--name-status", "--format=", "HEAD"],
                    cwd=repo_root,
                    capture_output=True,
                    text=True,
                    check=True,
                )
                .stdout.strip()
                .splitlines()
            )
            self.assertEqual(
                len(status_out), 1, f"Expected 1 rename line, got: {status_out}"
            )
            self.assertTrue(
                status_out[0].startswith("R"),
                f"Expected rename entry starting with 'R', got: {status_out[0]}",
            )
            self.assertIn("specs/draft/", status_out[0])
            self.assertIn("specs/to-review/", status_out[0])

    def test_self_commit_specs_set_positional_creates_single_rename_commit(
        self,
    ) -> None:
        """(b) aw specs set --dir <root> <s> <id6> --commit produces the same commit and single rename."""
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            _setup_test_repo(repo_root)

            proc = run_cli(
                "specs",
                "set",
                "--dir",
                str(repo_root),
                "to-review",
                "spc001",
                "--message",
                "move to to-review",
                "--commit",
                "--yes",
                cwd=repo_root,
            )
            self.assertEqual(
                proc.returncode, 0, f"stdout: {proc.stdout}\nstderr: {proc.stderr}"
            )

            # Check commit message
            msg = subprocess.run(
                ["git", "log", "-1", "--format=%s"],
                cwd=repo_root,
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip()
            self.assertEqual(msg, "chore(specs): set status to-review")

            # Check commit content is single rename
            status_out = (
                subprocess.run(
                    ["git", "show", "--name-status", "--format=", "HEAD"],
                    cwd=repo_root,
                    capture_output=True,
                    text=True,
                    check=True,
                )
                .stdout.strip()
                .splitlines()
            )
            self.assertEqual(
                len(status_out), 1, f"Expected 1 rename line, got: {status_out}"
            )
            self.assertTrue(
                status_out[0].startswith("R"),
                f"Expected rename entry starting with 'R', got: {status_out[0]}",
            )
            self.assertIn("specs/draft/", status_out[0])
            self.assertIn("specs/to-review/", status_out[0])

    def test_self_commit_unrelated_staged_file_preserved(self) -> None:
        """(c) with unrelated staged file present, neither spelling folds it in and it survives staged."""
        # Test --status spelling
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            paths = _setup_test_repo(repo_root)
            spec_path = paths["spec"]

            unrelated = repo_root / "unrelated.txt"
            unrelated.write_text("unrelated content\n", encoding="utf-8")
            subprocess.run(["git", "add", "unrelated.txt"], cwd=repo_root, check=True)

            proc = run_cli(
                "specs",
                "set",
                str(spec_path),
                "--status",
                "to-review",
                "--message",
                "transition with staged",
                "--commit",
                "--yes",
                cwd=repo_root,
            )
            self.assertEqual(
                proc.returncode, 0, f"stdout: {proc.stdout}\nstderr: {proc.stderr}"
            )

            # Must have created the commit for the spec
            msg = subprocess.run(
                ["git", "log", "-1", "--format=%s"],
                cwd=repo_root,
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip()
            self.assertEqual(msg, "chore(specs): set status to-review")

            committed_files = (
                subprocess.run(
                    ["git", "show", "--name-only", "--format=", "HEAD"],
                    cwd=repo_root,
                    capture_output=True,
                    text=True,
                    check=True,
                )
                .stdout.strip()
                .splitlines()
            )
            self.assertNotIn("unrelated.txt", committed_files)

            # Unrelated file must remain staged
            staged = (
                subprocess.run(
                    ["git", "diff", "--cached", "--name-only"],
                    cwd=repo_root,
                    capture_output=True,
                    text=True,
                    check=True,
                )
                .stdout.strip()
                .splitlines()
            )
            self.assertIn("unrelated.txt", staged)

        # Test positional spelling
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            _setup_test_repo(repo_root)

            unrelated = repo_root / "unrelated.txt"
            unrelated.write_text("unrelated content\n", encoding="utf-8")
            subprocess.run(["git", "add", "unrelated.txt"], cwd=repo_root, check=True)

            proc = run_cli(
                "specs",
                "set",
                "--dir",
                str(repo_root),
                "to-review",
                "spc001",
                "--message",
                "transition with staged",
                "--commit",
                "--yes",
                cwd=repo_root,
            )
            self.assertEqual(
                proc.returncode, 0, f"stdout: {proc.stdout}\nstderr: {proc.stderr}"
            )

            msg = subprocess.run(
                ["git", "log", "-1", "--format=%s"],
                cwd=repo_root,
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip()
            self.assertEqual(msg, "chore(specs): set status to-review")

            committed_files = (
                subprocess.run(
                    ["git", "show", "--name-only", "--format=", "HEAD"],
                    cwd=repo_root,
                    capture_output=True,
                    text=True,
                    check=True,
                )
                .stdout.strip()
                .splitlines()
            )
            self.assertNotIn("unrelated.txt", committed_files)

            staged = (
                subprocess.run(
                    ["git", "diff", "--cached", "--name-only"],
                    cwd=repo_root,
                    capture_output=True,
                    text=True,
                    check=True,
                )
                .stdout.strip()
                .splitlines()
            )
            self.assertIn("unrelated.txt", staged)

    def test_self_commit_no_commit_commits_nothing(self) -> None:
        """(d) --no-commit commits nothing on both spellings."""
        # --status spelling
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            paths = _setup_test_repo(repo_root)
            spec_path = paths["spec"]
            head_before = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=repo_root,
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip()

            proc = run_cli(
                "specs",
                "set",
                str(spec_path),
                "--status",
                "to-review",
                "--message",
                "no commit test",
                "--no-commit",
                "--yes",
                cwd=repo_root,
            )
            self.assertEqual(proc.returncode, 0)
            head_after = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=repo_root,
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip()
            self.assertEqual(head_before, head_after)

        # positional spelling
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            _setup_test_repo(repo_root)
            head_before = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=repo_root,
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip()

            proc = run_cli(
                "specs",
                "set",
                "--dir",
                str(repo_root),
                "to-review",
                "spc001",
                "--message",
                "no commit test",
                "--no-commit",
                "--yes",
                cwd=repo_root,
            )
            self.assertEqual(proc.returncode, 0)
            head_after = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=repo_root,
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip()
            self.assertEqual(head_before, head_after)

    def test_self_commit_yes_agent_does_not_commit(self) -> None:
        """(e) --yes without --commit and with --agent commits nothing on both spellings."""
        # --status spelling
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            paths = _setup_test_repo(repo_root)
            spec_path = paths["spec"]
            head_before = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=repo_root,
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip()

            proc = run_cli(
                "specs",
                "set",
                str(spec_path),
                "--status",
                "to-review",
                "--message",
                "agent test",
                "--yes",
                "--agent",
                cwd=repo_root,
            )
            self.assertEqual(proc.returncode, 0)
            head_after = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=repo_root,
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip()
            self.assertEqual(head_before, head_after)

        # positional spelling
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            _setup_test_repo(repo_root)
            head_before = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=repo_root,
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip()

            proc = run_cli(
                "specs",
                "set",
                "--dir",
                str(repo_root),
                "to-review",
                "spc001",
                "--message",
                "agent test",
                "--yes",
                "--agent",
                cwd=repo_root,
            )
            self.assertEqual(proc.returncode, 0)
            head_after = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=repo_root,
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip()
            self.assertEqual(head_before, head_after)


class TestFromBacklogInheritanceDedup(unittest.TestCase):
    """E-04: From-Backlog inheritance outcome tests across both dispatch spellings."""

    def test_inheritance_specs_set_status_notice_prefix(self) -> None:
        """(a) --status spelling inherits gate and prints 'aw specs set:' notice prefix."""
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            paths = _setup_test_repo(repo_root)
            spec_path = paths["spec"]

            proc = run_cli(
                "specs",
                "set",
                str(spec_path),
                "--status",
                "draft",
                "--from-backlog",
                "bkl001",
                "--message",
                "inherit gate",
                "--yes",
                "--no-commit",
                cwd=repo_root,
            )
            self.assertEqual(
                proc.returncode, 0, f"stdout: {proc.stdout}\nstderr: {proc.stderr}"
            )
            self.assertIn(
                "aw specs set: inherited - Blocks-Release: relaaa", proc.stdout
            )
            self.assertNotIn("aw set: inherited - Blocks-Release: relaaa", proc.stdout)

            content = spec_path.read_text(encoding="utf-8")
            self.assertIn("- From-Backlog: bkl001\n", content)
            self.assertIn("- Blocks-Release: relaaa\n", content)

    def test_inheritance_specs_set_positional_notice_prefix(self) -> None:
        """(b) positional spelling inherits gate and prints 'aw set:' notice prefix."""
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            paths = _setup_test_repo(repo_root)
            spec_path = paths["spec"]

            proc = run_cli(
                "specs",
                "set",
                "--dir",
                str(repo_root),
                "draft",
                "spc001",
                "--from-backlog",
                "bkl001",
                "--message",
                "inherit gate",
                "--yes",
                "--no-commit",
                cwd=repo_root,
            )
            self.assertEqual(
                proc.returncode, 0, f"stdout: {proc.stdout}\nstderr: {proc.stderr}"
            )
            self.assertIn("aw set: inherited - Blocks-Release: relaaa", proc.stdout)

            content = spec_path.read_text(encoding="utf-8")
            self.assertIn("- From-Backlog: bkl001\n", content)
            self.assertIn("- Blocks-Release: relaaa\n", content)

    def test_inheritance_explicit_blocks_release_wins(self) -> None:
        """(c) explicit --blocks-release in the same call wins over inheritance on both spellings."""
        # --status spelling with --blocks-release -
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            paths = _setup_test_repo(repo_root)
            spec_path = paths["spec"]

            proc = run_cli(
                "specs",
                "set",
                str(spec_path),
                "--status",
                "draft",
                "--from-backlog",
                "bkl001",
                "--blocks-release",
                "-",
                "--message",
                "explicit clear wins",
                "--yes",
                "--no-commit",
                cwd=repo_root,
            )
            self.assertEqual(proc.returncode, 0)
            self.assertNotIn("inherited - Blocks-Release:", proc.stdout)
            content = spec_path.read_text(encoding="utf-8")
            self.assertIn("- From-Backlog: bkl001\n", content)
            self.assertNotIn("- Blocks-Release:", content)

        # positional spelling with --blocks-release -
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            paths = _setup_test_repo(repo_root)
            spec_path = paths["spec"]

            proc = run_cli(
                "specs",
                "set",
                "--dir",
                str(repo_root),
                "draft",
                "spc001",
                "--from-backlog",
                "bkl001",
                "--blocks-release",
                "-",
                "--message",
                "explicit clear wins",
                "--yes",
                "--no-commit",
                cwd=repo_root,
            )
            self.assertEqual(proc.returncode, 0)
            self.assertNotIn("inherited - Blocks-Release:", proc.stdout)
            content = spec_path.read_text(encoding="utf-8")
            self.assertIn("- From-Backlog: bkl001\n", content)
            self.assertNotIn("- Blocks-Release:", content)

    def test_inheritance_existing_gate_preserved(self) -> None:
        """(d) an artifact that already carries a - Blocks-Release: keeps its own value on both spellings."""
        # --status spelling
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            paths = _setup_test_repo(repo_root)
            spec_gtd = paths["spec_gated"]

            proc = run_cli(
                "specs",
                "set",
                str(spec_gtd),
                "--status",
                "draft",
                "--from-backlog",
                "bkl001",
                "--message",
                "keep existing gate",
                "--yes",
                "--no-commit",
                cwd=repo_root,
            )
            self.assertEqual(proc.returncode, 0)
            self.assertNotIn("inherited - Blocks-Release:", proc.stdout)
            content = spec_gtd.read_text(encoding="utf-8")
            self.assertIn("- From-Backlog: bkl001\n", content)
            self.assertIn("- Blocks-Release: relorig\n", content)
            self.assertNotIn("relaaa", content)

        # positional spelling
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            paths = _setup_test_repo(repo_root)
            spec_gtd = paths["spec_gated"]

            proc = run_cli(
                "specs",
                "set",
                "--dir",
                str(repo_root),
                "draft",
                "spcgtd",
                "--from-backlog",
                "bkl001",
                "--message",
                "keep existing gate",
                "--yes",
                "--no-commit",
                cwd=repo_root,
            )
            self.assertEqual(proc.returncode, 0)
            self.assertNotIn("inherited - Blocks-Release:", proc.stdout)
            content = spec_gtd.read_text(encoding="utf-8")
            self.assertIn("- From-Backlog: bkl001\n", content)
            self.assertIn("- Blocks-Release: relorig\n", content)
            self.assertNotIn("relaaa", content)

    def test_inheritance_resolvable_ungated_backlog_item(self) -> None:
        """(e) --from-backlog naming a resolvable ungated item exits 0, writes From-Backlog, and writes no gate."""
        # --status spelling
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            paths = _setup_test_repo(repo_root)
            spec_path = paths["spec"]

            proc = run_cli(
                "specs",
                "set",
                str(spec_path),
                "--status",
                "draft",
                "--from-backlog",
                "bklung",
                "--message",
                "resolvable ungated",
                "--yes",
                "--no-commit",
                cwd=repo_root,
            )
            self.assertEqual(
                proc.returncode, 0, f"stdout: {proc.stdout}\nstderr: {proc.stderr}"
            )
            self.assertNotIn("inherited - Blocks-Release:", proc.stdout)
            content = spec_path.read_text(encoding="utf-8")
            self.assertIn("- From-Backlog: bklung\n", content)
            self.assertNotIn("- Blocks-Release:", content)

        # positional spelling
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            paths = _setup_test_repo(repo_root)
            spec_path = paths["spec"]

            proc = run_cli(
                "specs",
                "set",
                "--dir",
                str(repo_root),
                "draft",
                "spc001",
                "--from-backlog",
                "bklung",
                "--message",
                "resolvable ungated",
                "--yes",
                "--no-commit",
                cwd=repo_root,
            )
            self.assertEqual(
                proc.returncode, 0, f"stdout: {proc.stdout}\nstderr: {proc.stderr}"
            )
            self.assertNotIn("inherited - Blocks-Release:", proc.stdout)
            content = spec_path.read_text(encoding="utf-8")
            self.assertIn("- From-Backlog: bklung\n", content)
            self.assertNotIn("- Blocks-Release:", content)
