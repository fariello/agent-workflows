"""Outcome tests for repaired releases line writers (IPD izh17y).

Verifies that set_blocks_release_line and set_from_backlog_line:
1. Replace rather than duplicate an existing empty-valued line.
2. Replace rather than duplicate a whitespace-only valued line.
3. Replace a normally-valued existing line.
4. Insert immediately after - Status: when absent, preserving adjacent lines.
5. Fall back to inserting after - Id: when no - Status: exists.
6. Are byte-identical on repeated calls with the same value.
7. Remove the line and leave NO residue when called with '-' or None (including on empty-valued input).
8. Repair an already-corrupt duplicated record to exactly one line.
9. Leave surrounding metadata bullets intact.

Verifies CLI refusals for unresolvable --from-backlog (E-05):
10. `aw ipd set` refuses an unresolvable backlog ID with nonzero exit, names it, and leaves file byte-identical.
11. `aw ipd set` with resolvable backlog ID writes From-Backlog and inherits Blocks-Release with notice.
12. `aw ipd set --from-backlog -` clears the field.
13. `aw specs set --status` refuses an unresolvable backlog ID with nonzero exit, names it, and leaves file byte-identical.
14. `aw specs set --status` with resolvable backlog ID writes From-Backlog and inherits Blocks-Release with notice.
15. `aw specs set --status --from-backlog -` clears the field.
16. Empty backlog corpus fail-safe: in a repo with no backlog tree, writing succeeds rather than refusing.

Tests outcomes and behavior only; does not inspect source code structure.
"""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from agent_workflows import releases
from tests.support import run_cli


class TestSetBlocksReleaseLine(unittest.TestCase):
    """E-02 / V-01 / V-02: tests for releases.set_blocks_release_line."""

    def test_blocks_release_empty_value_replaced(self) -> None:
        """An empty-valued - Blocks-Release: line is replaced, resulting in exactly one line."""
        text = (
            "# Plan\n\n"
            "- Date: 2026-09-30\n"
            "- Status: open\n"
            "- Blocks-Release:\n"
            "- Id: aaaaaa\n"
        )
        result = releases.set_blocks_release_line(text, "next")
        self.assertEqual(result.count("- Blocks-Release:"), 1)
        expected = (
            "# Plan\n\n"
            "- Date: 2026-09-30\n"
            "- Status: open\n"
            "- Blocks-Release: next\n"
            "- Id: aaaaaa\n"
        )
        self.assertEqual(result, expected)

    def test_blocks_release_whitespace_value_replaced(self) -> None:
        """A whitespace-only - Blocks-Release: line is replaced, resulting in exactly one line."""
        text = (
            "# Plan\n\n"
            "- Date: 2026-09-30\n"
            "- Status: open\n"
            "- Blocks-Release:   \n"
            "- Id: aaaaaa\n"
        )
        result = releases.set_blocks_release_line(text, "next")
        self.assertEqual(result.count("- Blocks-Release:"), 1)
        expected = (
            "# Plan\n\n"
            "- Date: 2026-09-30\n"
            "- Status: open\n"
            "- Blocks-Release: next\n"
            "- Id: aaaaaa\n"
        )
        self.assertEqual(result, expected)

    def test_blocks_release_normally_valued_replaced(self) -> None:
        """A normally-valued - Blocks-Release: line is replaced with the new value."""
        text = (
            "# Plan\n\n"
            "- Date: 2026-09-30\n"
            "- Status: open\n"
            "- Blocks-Release: old123\n"
            "- Id: aaaaaa\n"
        )
        result = releases.set_blocks_release_line(text, "next")
        self.assertEqual(result.count("- Blocks-Release:"), 1)
        expected = (
            "# Plan\n\n"
            "- Date: 2026-09-30\n"
            "- Status: open\n"
            "- Blocks-Release: next\n"
            "- Id: aaaaaa\n"
        )
        self.assertEqual(result, expected)

    def test_blocks_release_absent_inserted_after_status(self) -> None:
        """An absent line is inserted immediately after - Status:, preserving surrounding bullets."""
        text = "# Plan\n\n" "- Date: 2026-09-30\n" "- Status: open\n" "- Id: aaaaaa\n"
        result = releases.set_blocks_release_line(text, "next")
        self.assertEqual(result.count("- Blocks-Release:"), 1)
        self.assertIn("- Status: open\n- Blocks-Release: next\n- Id: aaaaaa\n", result)

    def test_blocks_release_fallback_after_id(self) -> None:
        """When - Status: is absent, insertion falls back to immediately after - Id:."""
        text = "# Plan\n\n" "- Date: 2026-09-30\n" "- Id: aaaaaa\n" "- Scope: test\n"
        result = releases.set_blocks_release_line(text, "next")
        self.assertEqual(result.count("- Blocks-Release:"), 1)
        self.assertIn("- Id: aaaaaa\n- Blocks-Release: next\n- Scope: test\n", result)

    def test_blocks_release_idempotent(self) -> None:
        """Calling set_blocks_release_line twice with the same value is byte-identical."""
        text = "# Plan\n\n" "- Date: 2026-09-30\n" "- Status: open\n" "- Id: aaaaaa\n"
        first = releases.set_blocks_release_line(text, "next")
        second = releases.set_blocks_release_line(first, "next")
        self.assertEqual(first, second)

    def test_blocks_release_clear_dash_and_none(self) -> None:
        """'-' and None remove - Blocks-Release: and leave NO residue, even from empty-valued lines."""
        for initial in (
            "- Date: 2026-09-30\n- Status: open\n- Blocks-Release: next\n- Id: aaaaaa\n",
            "- Date: 2026-09-30\n- Status: open\n- Blocks-Release:\n- Id: aaaaaa\n",
            "- Date: 2026-09-30\n- Status: open\n- Blocks-Release:   \n- Id: aaaaaa\n",
        ):
            cleared_dash = releases.set_blocks_release_line(initial, "-")
            self.assertEqual(cleared_dash.count("- Blocks-Release:"), 0)
            self.assertIn("- Status: open\n- Id: aaaaaa\n", cleared_dash)

            cleared_none = releases.set_blocks_release_line(initial, None)
            self.assertEqual(cleared_none.count("- Blocks-Release:"), 0)
            self.assertIn("- Status: open\n- Id: aaaaaa\n", cleared_none)

    def test_blocks_release_repair_duplicate(self) -> None:
        """A text that already carries the duplicate corruption is healed to exactly one line."""
        text = (
            "# Plan\n\n"
            "- Date: 2026-09-30\n"
            "- Status: open\n"
            "- Blocks-Release:\n"
            "- Blocks-Release: old123\n"
            "- Id: aaaaaa\n"
        )
        result = releases.set_blocks_release_line(text, "next")
        self.assertEqual(result.count("- Blocks-Release:"), 1)
        expected = (
            "# Plan\n\n"
            "- Date: 2026-09-30\n"
            "- Status: open\n"
            "- Blocks-Release: next\n"
            "- Id: aaaaaa\n"
        )
        self.assertEqual(result, expected)


class TestSetFromBacklogLine(unittest.TestCase):
    """E-02 / V-01 / V-02: tests for releases.set_from_backlog_line."""

    def test_from_backlog_empty_value_replaced(self) -> None:
        """An empty-valued - From-Backlog: line is replaced, resulting in exactly one line."""
        text = (
            "# Plan\n\n"
            "- Date: 2026-09-30\n"
            "- Status: to-review\n"
            "- From-Backlog:\n"
            "- Id: abc123\n"
        )
        result = releases.set_from_backlog_line(text, "zzz999")
        self.assertEqual(result.count("- From-Backlog:"), 1)
        expected = (
            "# Plan\n\n"
            "- Date: 2026-09-30\n"
            "- Status: to-review\n"
            "- From-Backlog: zzz999\n"
            "- Id: abc123\n"
        )
        self.assertEqual(result, expected)

    def test_from_backlog_whitespace_value_replaced(self) -> None:
        """A whitespace-only - From-Backlog: line is replaced, resulting in exactly one line."""
        text = (
            "# Plan\n\n"
            "- Date: 2026-09-30\n"
            "- Status: to-review\n"
            "- From-Backlog:   \n"
            "- Id: abc123\n"
        )
        result = releases.set_from_backlog_line(text, "zzz999")
        self.assertEqual(result.count("- From-Backlog:"), 1)
        expected = (
            "# Plan\n\n"
            "- Date: 2026-09-30\n"
            "- Status: to-review\n"
            "- From-Backlog: zzz999\n"
            "- Id: abc123\n"
        )
        self.assertEqual(result, expected)

    def test_from_backlog_normally_valued_replaced(self) -> None:
        """A normally-valued - From-Backlog: line is replaced with the new value."""
        text = (
            "# Plan\n\n"
            "- Date: 2026-09-30\n"
            "- Status: to-review\n"
            "- From-Backlog: old123\n"
            "- Id: abc123\n"
        )
        result = releases.set_from_backlog_line(text, "zzz999")
        self.assertEqual(result.count("- From-Backlog:"), 1)
        expected = (
            "# Plan\n\n"
            "- Date: 2026-09-30\n"
            "- Status: to-review\n"
            "- From-Backlog: zzz999\n"
            "- Id: abc123\n"
        )
        self.assertEqual(result, expected)

    def test_from_backlog_absent_inserted_after_status(self) -> None:
        """An absent line is inserted immediately after - Status:, preserving surrounding bullets."""
        text = (
            "# Plan\n\n" "- Date: 2026-09-30\n" "- Status: to-review\n" "- Id: abc123\n"
        )
        result = releases.set_from_backlog_line(text, "zzz999")
        self.assertEqual(result.count("- From-Backlog:"), 1)
        self.assertIn(
            "- Status: to-review\n- From-Backlog: zzz999\n- Id: abc123\n", result
        )

    def test_from_backlog_fallback_after_id(self) -> None:
        """When - Status: is absent, insertion falls back to immediately after - Id:."""
        text = "# Plan\n\n" "- Date: 2026-09-30\n" "- Id: abc123\n" "- Scope: test\n"
        result = releases.set_from_backlog_line(text, "zzz999")
        self.assertEqual(result.count("- From-Backlog:"), 1)
        self.assertIn("- Id: abc123\n- From-Backlog: zzz999\n- Scope: test\n", result)

    def test_from_backlog_idempotent(self) -> None:
        """Calling set_from_backlog_line twice with the same value is byte-identical."""
        text = (
            "# Plan\n\n" "- Date: 2026-09-30\n" "- Status: to-review\n" "- Id: abc123\n"
        )
        first = releases.set_from_backlog_line(text, "zzz999")
        second = releases.set_from_backlog_line(first, "zzz999")
        self.assertEqual(first, second)

    def test_from_backlog_clear_dash_and_none(self) -> None:
        """'-' and None remove - From-Backlog: and leave NO residue, even from empty-valued lines."""
        for initial in (
            "- Date: 2026-09-30\n- Status: to-review\n- From-Backlog: zzz999\n- Id: abc123\n",
            "- Date: 2026-09-30\n- Status: to-review\n- From-Backlog:\n- Id: abc123\n",
            "- Date: 2026-09-30\n- Status: to-review\n- From-Backlog:   \n- Id: abc123\n",
        ):
            cleared_dash = releases.set_from_backlog_line(initial, "-")
            self.assertEqual(cleared_dash.count("- From-Backlog:"), 0)
            self.assertIn("- Status: to-review\n- Id: abc123\n", cleared_dash)

            cleared_none = releases.set_from_backlog_line(initial, None)
            self.assertEqual(cleared_none.count("- From-Backlog:"), 0)
            self.assertIn("- Status: to-review\n- Id: abc123\n", cleared_none)

    def test_from_backlog_repair_duplicate(self) -> None:
        """A text that already carries the duplicate corruption is healed to exactly one line."""
        text = (
            "# Plan\n\n"
            "- Date: 2026-09-30\n"
            "- Status: to-review\n"
            "- From-Backlog:\n"
            "- From-Backlog: old123\n"
            "- Id: abc123\n"
        )
        result = releases.set_from_backlog_line(text, "zzz999")
        self.assertEqual(result.count("- From-Backlog:"), 1)
        expected = (
            "# Plan\n\n"
            "- Date: 2026-09-30\n"
            "- Status: to-review\n"
            "- From-Backlog: zzz999\n"
            "- Id: abc123\n"
        )
        self.assertEqual(result, expected)


def _setup_test_repo(root: Path, *, with_backlog: bool = True) -> dict[str, Path]:
    """Helper to initialize a temporary git repo with valid planned release, plan, and optional backlog/spec."""
    subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
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
    if with_backlog:
        bk_dir = root / ".aw" / "records" / "backlog" / "open"
        bk_dir.mkdir(parents=True, exist_ok=True)
        bk_path = bk_dir / "20260930-bkl001-01-bkl001-test-bug.backlog.md"
        bk_path.write_text(
            "- Id: bkl001\n"
            "- Status: open\n"
            "- Priority: medium\n"
            "- Work-Kind: bug\n"
            "- Blocks-Release: relaaa\n"
            "- Summary: Test bug\n\n"
            "## Workflow history\n"
            "- 2026-09-30 open (tester): created\n",
            encoding="utf-8",
        )
        paths["backlog"] = bk_path

    # Release relaaa (active planned release)
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

    # Plan
    plan_dir = root / ".aw" / "records" / "plans" / "pending"
    plan_dir.mkdir(parents=True, exist_ok=True)
    plan_path = plan_dir / "20260930-testset-01-pln001-test-plan.ipd.md"
    plan_path.write_text(
        "# Plan: Test Plan\n\n"
        "- Date: 2026-09-30\n"
        "- Kind: child\n"
        "- Concern: test concern\n"
        "- Scope: test scope\n"
        "- Scope-Paths: test.py\n"
        "- Item-Dependencies: none\n"
        "- Status: to-review\n"
        "- Work-Kind: bug\n"
        "- Priority: medium\n"
        "- Set: testset\n"
        "- Order: 1\n"
        "- Id: pln001\n\n"
        "## Workflow history\n"
        "- 2026-09-30 to-review (tester): created\n",
        encoding="utf-8",
    )
    paths["plan"] = plan_path

    # Spec
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

    subprocess.run(["git", "add", "-A"], cwd=root, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "init repo"], cwd=root, check=True, capture_output=True
    )
    return paths


class TestCliIpdSetFromBacklog(unittest.TestCase):
    """E-05 / V-03 / V-05: aw ipd set --from-backlog CLI tests."""

    def test_cli_ipd_set_refuse_unresolvable_backlog_id(self) -> None:
        """An unresolvable backlog ID exits nonzero, names the value, and leaves the plan byte-identical."""
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            paths = _setup_test_repo(repo_root)
            plan_path = paths["plan"]
            bytes_before = plan_path.read_bytes()

            proc = run_cli(
                "ipd",
                "set",
                "--dir",
                str(repo_root),
                "to-review",
                "pln001",
                "--from-backlog",
                "nosuch",
                "--yes",
                "--no-commit",
                cwd=repo_root,
            )
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("nosuch", proc.stdout + proc.stderr)
            bytes_after = plan_path.read_bytes()
            self.assertEqual(bytes_before, bytes_after)

    def test_cli_ipd_set_resolvable_backlog_id_writes_and_inherits_gate(self) -> None:
        """A resolvable backlog ID writes From-Backlog and inherits Blocks-Release with stdout notice."""
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            paths = _setup_test_repo(repo_root)
            plan_path = paths["plan"]

            proc = run_cli(
                "ipd",
                "set",
                "--dir",
                str(repo_root),
                "to-review",
                "pln001",
                "--from-backlog",
                "bkl001",
                "--yes",
                "--no-commit",
                cwd=repo_root,
            )
            self.assertEqual(proc.returncode, 0)
            self.assertIn("aw set: inherited - Blocks-Release: relaaa", proc.stdout)
            content = plan_path.read_text(encoding="utf-8")
            self.assertIn("- From-Backlog: bkl001\n", content)
            self.assertIn("- Blocks-Release: relaaa\n", content)

    def test_cli_ipd_set_clear_from_backlog_with_dash(self) -> None:
        """`--from-backlog -` clears the From-Backlog field."""
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            paths = _setup_test_repo(repo_root)
            plan_path = paths["plan"]

            # First write a valid From-Backlog
            res1 = run_cli(
                "ipd",
                "set",
                "--dir",
                str(repo_root),
                "to-review",
                "pln001",
                "--from-backlog",
                "bkl001",
                "--yes",
                "--no-commit",
                cwd=repo_root,
            )
            self.assertEqual(res1.returncode, 0)
            self.assertIn(
                "- From-Backlog: bkl001\n", plan_path.read_text(encoding="utf-8")
            )

            # Clear with -
            proc = run_cli(
                "ipd",
                "set",
                "--dir",
                str(repo_root),
                "to-review",
                "pln001",
                "--from-backlog",
                "-",
                "--yes",
                "--no-commit",
                cwd=repo_root,
            )
            self.assertEqual(proc.returncode, 0)
            self.assertNotIn("- From-Backlog:", plan_path.read_text(encoding="utf-8"))


class TestCliSpecsSetFromBacklog(unittest.TestCase):
    """E-05 / V-04 / V-05: aw specs set --status --from-backlog CLI tests (forked surface)."""

    def test_cli_specs_set_refuse_unresolvable_backlog_id(self) -> None:
        """An unresolvable backlog ID exits nonzero, names the value, and leaves the spec byte-identical."""
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            paths = _setup_test_repo(repo_root)
            spec_path = paths["spec"]
            bytes_before = spec_path.read_bytes()

            proc = run_cli(
                "specs",
                "set",
                str(spec_path),
                "--status",
                "draft",
                "--from-backlog",
                "nosuch",
                "--message",
                "test unresolvable refusal",
                "--yes",
                "--no-commit",
                cwd=repo_root,
            )
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("nosuch", proc.stdout + proc.stderr)
            bytes_after = spec_path.read_bytes()
            self.assertEqual(bytes_before, bytes_after)

    def test_cli_specs_set_resolvable_backlog_id_writes_and_inherits_gate(self) -> None:
        """A resolvable backlog ID writes From-Backlog and inherits Blocks-Release with stdout notice."""
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
                "test resolvable link",
                "--yes",
                "--no-commit",
                cwd=repo_root,
            )
            self.assertEqual(proc.returncode, 0)
            self.assertIn("aw set: inherited - Blocks-Release: relaaa", proc.stdout)
            content = spec_path.read_text(encoding="utf-8")
            self.assertIn("- From-Backlog: bkl001\n", content)
            self.assertIn("- Blocks-Release: relaaa\n", content)

    def test_cli_specs_set_clear_from_backlog_with_dash(self) -> None:
        """`--from-backlog -` clears the From-Backlog field on specs set --status."""
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            paths = _setup_test_repo(repo_root)
            spec_path = paths["spec"]

            # First write a valid From-Backlog
            res1 = run_cli(
                "specs",
                "set",
                str(spec_path),
                "--status",
                "draft",
                "--from-backlog",
                "bkl001",
                "--message",
                "test link before clear",
                "--yes",
                "--no-commit",
                cwd=repo_root,
            )
            self.assertEqual(res1.returncode, 0)
            self.assertIn(
                "- From-Backlog: bkl001\n", spec_path.read_text(encoding="utf-8")
            )

            # Clear with -
            proc = run_cli(
                "specs",
                "set",
                str(spec_path),
                "--status",
                "draft",
                "--from-backlog",
                "-",
                "--message",
                "clear link",
                "--yes",
                "--no-commit",
                cwd=repo_root,
            )
            self.assertEqual(proc.returncode, 0)
            self.assertNotIn("- From-Backlog:", spec_path.read_text(encoding="utf-8"))


class TestCliEmptyBacklogFailSafe(unittest.TestCase):
    """E-05 / V-05: Empty-set fail-safe tests."""

    def test_cli_empty_backlog_corpus_failsafe_allows_write(self) -> None:
        """In a repository with no backlog tree at all, a --from-backlog write succeeds rather
        than refusing (fail-safe for invisible corpus).

        NOTE ON DELIBERATE DIVERGENCE (F-12): on this same tree, releases.check_from_backlog
        reports the value as dangling at error, because that function has no empty-set guard
        and its own docstring records the asymmetry ('the less safe twin') and forbids
        harmonizing it away.
        """
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            # Create repo with NO backlog tree
            paths = _setup_test_repo(repo_root, with_backlog=False)
            plan_path = paths["plan"]

            proc = run_cli(
                "ipd",
                "set",
                "--dir",
                str(repo_root),
                "to-review",
                "pln001",
                "--from-backlog",
                "anyval",
                "--yes",
                "--no-commit",
                cwd=repo_root,
            )
            self.assertEqual(proc.returncode, 0)
            content = plan_path.read_text(encoding="utf-8")
            self.assertIn("- From-Backlog: anyval\n", content)


if __name__ == "__main__":
    unittest.main()
