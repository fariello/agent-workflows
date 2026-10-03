"""Tests for gatefollows vsgd48: Default release gate when a bug transitions into a live status.

Covers:
- E-03: Five routes into 'live and ungated', for BOTH spellings of `aw backlog set`:
  (a) reclassification `chore -> bug` while `open` (already passing, F-01/F-02 regression pin)
  (b) `open -> graduated` on an ungated bug (F-03)
  (c) `parked -> open` on an ungated bug (F-04)
  (d) `done -> open` on an ungated bug (F-05)
  (e) transition into `blocked` on an ungated bug (F-11)
- E-04: Three negative fence properties for both spellings:
  (a) explicit `--blocks-release -` leaves item ungated (condition 4)
  (b) existing gate `- Blocks-Release: <id6>` is preserved and not overwritten with `next`
  (c) transition to `done` or `parked` writes no gate (condition 3 / skip statuses)
"""

from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from agent_workflows import check_engine, cli


def _setup_repo(root: Path) -> Path:
    """Create a minimal repository structure with planned release."""
    for sub in ("open", "parked", "graduated", "done", "blocked"):
        (root / ".aw" / "records" / "backlog" / sub).mkdir(parents=True, exist_ok=True)
    (root / ".aw" / "records" / "releases").mkdir(parents=True, exist_ok=True)
    rel = (
        root
        / ".aw"
        / "records"
        / "releases"
        / "20260901-rel001-01-rel001-v1.release.md"
    )
    rel.write_text(
        "# Release: 1.0.0\n\n"
        "- Id: rel001\n"
        "- Status: planned\n"
        "- Version: 1.0.0\n"
        "- Summary: Test release\n",
        encoding="utf-8",
    )
    return root


def _create_item(
    repo: Path,
    *,
    status: str,
    work_kind: str,
    item_id: str = "bk0001",
    blocks_release: str | None = None,
) -> Path:
    """Create a backlog item in the given status."""
    lines = [
        f"- Id: {item_id}",
        f"- Status: {status}",
    ]
    if blocks_release is not None:
        lines.append(f"- Blocks-Release: {blocks_release}")
    lines.extend(
        [
            f"- Set: {item_id}",
            "- Priority: medium",
            f"- Work-Kind: {work_kind}",
            "- Summary: Test defect",
            "",
            "## Workflow history",
            "- 2026-09-28 created (tester): initial",
            "",
        ]
    )
    p = (
        repo
        / ".aw"
        / "records"
        / "backlog"
        / status
        / f"20260928-{item_id}-01-{item_id}-test.backlog.md"
    )
    p.write_text("\n".join(lines), encoding="utf-8")
    return p


def _find_item(repo: Path, item_id: str) -> Path:
    """Locate the item file regardless of which status directory it moved into."""
    matches = list(
        (repo / ".aw" / "records" / "backlog").rglob(f"*{item_id}*.backlog.md")
    )
    if not matches:
        matches = list((repo / ".aw" / "records" / "backlog").rglob(f"*{item_id}*.md"))
    assert matches, f"Could not find item {item_id} in {repo}"
    return matches[0]


class TestBacklogGateFollowsStatus(unittest.TestCase):
    """Pin the five live routes and three negative fence properties."""

    # =========================================================================
    # E-03 Route (a): reclassification chore -> bug while open (regression pin)
    # =========================================================================

    def test_route_a_reclassification_chore_to_bug_status_spelling(self) -> None:
        """Route (a) --status spelling: reclassification chore -> bug while open defaults gate."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = _setup_repo(Path(tmp))
            item_path = _create_item(
                repo, status="open", work_kind="chore", item_id="bk0001"
            )

            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                rc = cli.main(
                    [
                        "backlog",
                        "set",
                        str(item_path),
                        "--status",
                        "open",
                        "--work-kind",
                        "bug",
                        "--no-commit",
                        "--dir",
                        str(repo),
                    ]
                )
            self.assertEqual(rc, 0, f"Command failed: {err.getvalue()}")
            updated = _find_item(repo, "bk0001").read_text(encoding="utf-8")
            self.assertIn("- Blocks-Release: next", updated)
            findings = check_engine.check_live_bug_gate(repo)
            self.assertEqual(findings, [])

    def test_route_a_reclassification_chore_to_bug_positional_spelling(self) -> None:
        """Route (a) positional spelling: reclassification chore -> bug while open defaults gate."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = _setup_repo(Path(tmp))
            _create_item(repo, status="open", work_kind="chore", item_id="bk0001")

            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                rc = cli.main(
                    [
                        "backlog",
                        "set",
                        "open",
                        "bk0001",
                        "--work-kind",
                        "bug",
                        "--yes",
                        "--no-commit",
                        "--dir",
                        str(repo),
                    ]
                )
            self.assertEqual(rc, 0, f"Command failed: {err.getvalue()}")
            updated = _find_item(repo, "bk0001").read_text(encoding="utf-8")
            self.assertIn("- Blocks-Release: next", updated)
            findings = check_engine.check_live_bug_gate(repo)
            self.assertEqual(findings, [])

    # =========================================================================
    # E-03 Route (b): open -> graduated on an ungated bug
    # =========================================================================

    def test_route_b_open_to_graduated_status_spelling(self) -> None:
        """Route (b) --status spelling: open -> graduated on an ungated bug defaults gate."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = _setup_repo(Path(tmp))
            item_path = _create_item(
                repo, status="open", work_kind="bug", item_id="bk0002"
            )

            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                rc = cli.main(
                    [
                        "backlog",
                        "set",
                        str(item_path),
                        "--status",
                        "graduated",
                        "--no-commit",
                        "--dir",
                        str(repo),
                    ]
                )
            self.assertEqual(rc, 0, f"Command failed: {err.getvalue()}")
            updated = _find_item(repo, "bk0002").read_text(encoding="utf-8")
            self.assertIn("- Blocks-Release: next", updated)
            findings = check_engine.check_live_bug_gate(repo)
            self.assertEqual(findings, [])

    def test_route_b_open_to_graduated_positional_spelling(self) -> None:
        """Route (b) positional spelling: open -> graduated on an ungated bug defaults gate."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = _setup_repo(Path(tmp))
            _create_item(repo, status="open", work_kind="bug", item_id="bk0002")

            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                rc = cli.main(
                    [
                        "backlog",
                        "set",
                        "graduated",
                        "bk0002",
                        "--yes",
                        "--no-commit",
                        "--dir",
                        str(repo),
                    ]
                )
            self.assertEqual(rc, 0, f"Command failed: {err.getvalue()}")
            updated = _find_item(repo, "bk0002").read_text(encoding="utf-8")
            self.assertIn("- Blocks-Release: next", updated)
            findings = check_engine.check_live_bug_gate(repo)
            self.assertEqual(findings, [])

    # =========================================================================
    # E-03 Route (c): parked -> open on an ungated bug
    # =========================================================================

    def test_route_c_parked_to_open_status_spelling(self) -> None:
        """Route (c) --status spelling: parked -> open on an ungated bug defaults gate."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = _setup_repo(Path(tmp))
            item_path = _create_item(
                repo, status="parked", work_kind="bug", item_id="bk0003"
            )

            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                rc = cli.main(
                    [
                        "backlog",
                        "set",
                        str(item_path),
                        "--status",
                        "open",
                        "--no-commit",
                        "--dir",
                        str(repo),
                    ]
                )
            self.assertEqual(rc, 0, f"Command failed: {err.getvalue()}")
            updated = _find_item(repo, "bk0003").read_text(encoding="utf-8")
            self.assertIn("- Blocks-Release: next", updated)
            findings = check_engine.check_live_bug_gate(repo)
            self.assertEqual(findings, [])

    def test_route_c_parked_to_open_positional_spelling(self) -> None:
        """Route (c) positional spelling: parked -> open on an ungated bug defaults gate."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = _setup_repo(Path(tmp))
            _create_item(repo, status="parked", work_kind="bug", item_id="bk0003")

            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                rc = cli.main(
                    [
                        "backlog",
                        "set",
                        "open",
                        "bk0003",
                        "--yes",
                        "--no-commit",
                        "--dir",
                        str(repo),
                    ]
                )
            self.assertEqual(rc, 0, f"Command failed: {err.getvalue()}")
            updated = _find_item(repo, "bk0003").read_text(encoding="utf-8")
            self.assertIn("- Blocks-Release: next", updated)
            findings = check_engine.check_live_bug_gate(repo)
            self.assertEqual(findings, [])

    # =========================================================================
    # E-03 Route (d): done -> open on an ungated bug
    # =========================================================================

    def test_route_d_done_to_open_status_spelling(self) -> None:
        """Route (d) --status spelling: done -> open on an ungated bug defaults gate."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = _setup_repo(Path(tmp))
            item_path = _create_item(
                repo, status="done", work_kind="bug", item_id="bk0004"
            )

            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                rc = cli.main(
                    [
                        "backlog",
                        "set",
                        str(item_path),
                        "--status",
                        "open",
                        "--no-commit",
                        "--dir",
                        str(repo),
                    ]
                )
            self.assertEqual(rc, 0, f"Command failed: {err.getvalue()}")
            updated = _find_item(repo, "bk0004").read_text(encoding="utf-8")
            self.assertIn("- Blocks-Release: next", updated)
            findings = check_engine.check_live_bug_gate(repo)
            self.assertEqual(findings, [])

    def test_route_d_done_to_open_positional_spelling(self) -> None:
        """Route (d) positional spelling: done -> open on an ungated bug defaults gate."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = _setup_repo(Path(tmp))
            _create_item(repo, status="done", work_kind="bug", item_id="bk0004")

            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                rc = cli.main(
                    [
                        "backlog",
                        "set",
                        "open",
                        "bk0004",
                        "--yes",
                        "--no-commit",
                        "--dir",
                        str(repo),
                    ]
                )
            self.assertEqual(rc, 0, f"Command failed: {err.getvalue()}")
            updated = _find_item(repo, "bk0004").read_text(encoding="utf-8")
            self.assertIn("- Blocks-Release: next", updated)
            findings = check_engine.check_live_bug_gate(repo)
            self.assertEqual(findings, [])

    # =========================================================================
    # E-03 Route (e): transition into blocked on an ungated bug
    # =========================================================================

    def test_route_e_transition_to_blocked_status_spelling(self) -> None:
        """Route (e) --status spelling: transition into blocked on an ungated bug defaults gate."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = _setup_repo(Path(tmp))
            item_path = _create_item(
                repo, status="parked", work_kind="bug", item_id="bk0005"
            )

            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                rc = cli.main(
                    [
                        "backlog",
                        "set",
                        str(item_path),
                        "--status",
                        "blocked",
                        "--gate-kind",
                        "external",
                        "--gate-ref",
                        "Waiting on clarification",
                        "--no-commit",
                        "--dir",
                        str(repo),
                    ]
                )
            self.assertEqual(rc, 0, f"Command failed: {err.getvalue()}")
            updated = _find_item(repo, "bk0005").read_text(encoding="utf-8")
            self.assertIn("- Blocks-Release: next", updated)
            findings = check_engine.check_live_bug_gate(repo)
            self.assertEqual(findings, [])

    def test_route_e_transition_to_blocked_positional_spelling(self) -> None:
        """Route (e) positional spelling: transition into blocked on an ungated bug defaults gate."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = _setup_repo(Path(tmp))
            _create_item(repo, status="parked", work_kind="bug", item_id="bk0005")

            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                rc = cli.main(
                    [
                        "backlog",
                        "set",
                        "blocked",
                        "bk0005",
                        "--gate-kind",
                        "external",
                        "--gate-ref",
                        "Waiting on clarification",
                        "--yes",
                        "--no-commit",
                        "--dir",
                        str(repo),
                    ]
                )
            self.assertEqual(rc, 0, f"Command failed: {err.getvalue()}")
            updated = _find_item(repo, "bk0005").read_text(encoding="utf-8")
            self.assertIn("- Blocks-Release: next", updated)
            findings = check_engine.check_live_bug_gate(repo)
            self.assertEqual(findings, [])

    # =========================================================================
    # E-04 Negative Fences:
    # All three negatives already hold at this HEAD; they are fences ensuring
    # the broadened guard does not over-reach. Passes both before and after fix.
    # =========================================================================

    def test_negative_explicit_blocks_release_dash_wins_status_spelling(self) -> None:
        """FENCE: Explicit --blocks-release - leaves item ungated (--status spelling).

        Passes both before and after the fix (predicate condition 4, explicit value wins).
        """
        with tempfile.TemporaryDirectory() as tmp:
            repo = _setup_repo(Path(tmp))
            item_path = _create_item(
                repo, status="parked", work_kind="bug", item_id="bk0006"
            )

            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                rc = cli.main(
                    [
                        "backlog",
                        "set",
                        str(item_path),
                        "--status",
                        "open",
                        "--blocks-release",
                        "-",
                        "--no-commit",
                        "--dir",
                        str(repo),
                    ]
                )
            self.assertEqual(rc, 0, f"Command failed: {err.getvalue()}")
            updated = _find_item(repo, "bk0006").read_text(encoding="utf-8")
            self.assertNotIn("Blocks-Release", updated)

    def test_negative_explicit_blocks_release_dash_wins_positional_spelling(
        self,
    ) -> None:
        """FENCE: Explicit --blocks-release - leaves item ungated (positional spelling).

        Passes both before and after the fix (predicate condition 4, explicit value wins).
        """
        with tempfile.TemporaryDirectory() as tmp:
            repo = _setup_repo(Path(tmp))
            _create_item(repo, status="parked", work_kind="bug", item_id="bk0006")

            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                rc = cli.main(
                    [
                        "backlog",
                        "set",
                        "open",
                        "bk0006",
                        "--blocks-release",
                        "-",
                        "--yes",
                        "--no-commit",
                        "--dir",
                        str(repo),
                    ]
                )
            self.assertEqual(rc, 0, f"Command failed: {err.getvalue()}")
            updated = _find_item(repo, "bk0006").read_text(encoding="utf-8")
            self.assertNotIn("Blocks-Release", updated)

    def test_negative_existing_gate_preserved_status_spelling(self) -> None:
        """FENCE: Existing gate is preserved when transitioned (--status spelling).

        Passes both before and after the fix (existing gate is never rewritten to next).
        """
        with tempfile.TemporaryDirectory() as tmp:
            repo = _setup_repo(Path(tmp))
            item_path = _create_item(
                repo,
                status="parked",
                work_kind="bug",
                item_id="bk0007",
                blocks_release="rel001",
            )

            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                rc = cli.main(
                    [
                        "backlog",
                        "set",
                        str(item_path),
                        "--status",
                        "open",
                        "--no-commit",
                        "--dir",
                        str(repo),
                    ]
                )
            self.assertEqual(rc, 0, f"Command failed: {err.getvalue()}")
            updated = _find_item(repo, "bk0007").read_text(encoding="utf-8")
            self.assertIn("- Blocks-Release: rel001", updated)
            self.assertNotIn("- Blocks-Release: next", updated)

    def test_negative_existing_gate_preserved_positional_spelling(self) -> None:
        """FENCE: Existing gate is preserved when transitioned (positional spelling).

        Passes both before and after the fix (existing gate is never rewritten to next).
        """
        with tempfile.TemporaryDirectory() as tmp:
            repo = _setup_repo(Path(tmp))
            _create_item(
                repo,
                status="parked",
                work_kind="bug",
                item_id="bk0007",
                blocks_release="rel001",
            )

            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                rc = cli.main(
                    [
                        "backlog",
                        "set",
                        "open",
                        "bk0007",
                        "--yes",
                        "--no-commit",
                        "--dir",
                        str(repo),
                    ]
                )
            self.assertEqual(rc, 0, f"Command failed: {err.getvalue()}")
            updated = _find_item(repo, "bk0007").read_text(encoding="utf-8")
            self.assertIn("- Blocks-Release: rel001", updated)
            self.assertNotIn("- Blocks-Release: next", updated)

    def test_negative_transition_to_done_writes_no_gate_status_spelling(self) -> None:
        """FENCE: Transition to done writes no gate (--status spelling).

        Passes both before and after the fix (predicate condition 3 / _GATE_DEFAULT_SKIP_STATUSES).
        """
        with tempfile.TemporaryDirectory() as tmp:
            repo = _setup_repo(Path(tmp))
            item_path = _create_item(
                repo, status="open", work_kind="bug", item_id="bk0008"
            )

            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                rc = cli.main(
                    [
                        "backlog",
                        "set",
                        str(item_path),
                        "--status",
                        "done",
                        "--no-commit",
                        "--dir",
                        str(repo),
                    ]
                )
            self.assertEqual(rc, 0, f"Command failed: {err.getvalue()}")
            updated = _find_item(repo, "bk0008").read_text(encoding="utf-8")
            self.assertNotIn("Blocks-Release", updated)

    def test_negative_transition_to_done_writes_no_gate_positional_spelling(
        self,
    ) -> None:
        """FENCE: Transition to done writes no gate (positional spelling).

        Passes both before and after the fix (predicate condition 3 / _GATE_DEFAULT_SKIP_STATUSES).
        """
        with tempfile.TemporaryDirectory() as tmp:
            repo = _setup_repo(Path(tmp))
            _create_item(repo, status="open", work_kind="bug", item_id="bk0008")

            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                rc = cli.main(
                    [
                        "backlog",
                        "set",
                        "done",
                        "bk0008",
                        "--yes",
                        "--no-commit",
                        "--dir",
                        str(repo),
                    ]
                )
            self.assertEqual(rc, 0, f"Command failed: {err.getvalue()}")
            updated = _find_item(repo, "bk0008").read_text(encoding="utf-8")
            self.assertNotIn("Blocks-Release", updated)

    def test_negative_transition_to_parked_writes_no_gate_status_spelling(self) -> None:
        """FENCE: Transition to parked writes no gate (--status spelling).

        Passes both before and after the fix (predicate condition 3 / _GATE_DEFAULT_SKIP_STATUSES).
        """
        with tempfile.TemporaryDirectory() as tmp:
            repo = _setup_repo(Path(tmp))
            item_path = _create_item(
                repo, status="open", work_kind="bug", item_id="bk0009"
            )

            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                rc = cli.main(
                    [
                        "backlog",
                        "set",
                        str(item_path),
                        "--status",
                        "parked",
                        "--no-commit",
                        "--dir",
                        str(repo),
                    ]
                )
            self.assertEqual(rc, 0, f"Command failed: {err.getvalue()}")
            updated = _find_item(repo, "bk0009").read_text(encoding="utf-8")
            self.assertNotIn("Blocks-Release", updated)

    def test_negative_transition_to_parked_writes_no_gate_positional_spelling(
        self,
    ) -> None:
        """FENCE: Transition to parked writes no gate (positional spelling).

        Passes both before and after the fix (predicate condition 3 / _GATE_DEFAULT_SKIP_STATUSES).
        """
        with tempfile.TemporaryDirectory() as tmp:
            repo = _setup_repo(Path(tmp))
            _create_item(repo, status="open", work_kind="bug", item_id="bk0009")

            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                rc = cli.main(
                    [
                        "backlog",
                        "set",
                        "parked",
                        "bk0009",
                        "--yes",
                        "--no-commit",
                        "--dir",
                        str(repo),
                    ]
                )
            self.assertEqual(rc, 0, f"Command failed: {err.getvalue()}")
            updated = _find_item(repo, "bk0009").read_text(encoding="utf-8")
            self.assertNotIn("Blocks-Release", updated)


if __name__ == "__main__":
    unittest.main()
