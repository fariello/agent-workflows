"""Tests for gatebypass 47ttnv: Close-legitimacy predicate parity on positional aw backlog set.

Pins:
- E-01: Release-gate close-legitimacy check on the positional path (refusal exit 1, warn on parked)
- E-02: Post-mutation item text (same-call `--blocks-release -` de-gate, gate defaulting interaction)
- E-03: `--evidence` reaches predicate (SATISFIED success, unresolvable refusal, priority-demote warn)
- F-05: Dry-run refusal parity on illegitimate close
- F-06: Untyped `aw set done <id6>` refusal

All tests follow the paired-spelling pattern from tests/test_backlog_gate_follows_status.py,
testing both `_status_spelling` and `_positional_spelling` against identical fresh repos.
"""

from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from agent_workflows import cli


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
    priority: str = "medium",
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
            f"- Priority: {priority}",
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


class TestBacklogPositionalCloseGate(unittest.TestCase):
    """Paired-spelling tests pinning release-gate close-legitimacy parity."""

    # =========================================================================
    # V-01 / E-01: Ungated close refusal (no carrier, no evidence)
    # =========================================================================

    def test_ungated_close_refusal_status_spelling(self) -> None:
        """Status spelling refuses illegitimate close of release-gated item."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = _setup_repo(Path(tmp))
            item_path = _create_item(
                repo, status="open", work_kind="bug", blocks_release="next"
            )
            original_bytes = item_path.read_bytes()

            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                rc = cli.main(
                    [
                        "backlog",
                        "set",
                        str(item_path),
                        "--status",
                        "done",
                        "--yes",
                        "--no-commit",
                        "--dir",
                        str(repo),
                    ]
                )
            self.assertEqual(rc, 1)
            found = _find_item(repo, "bk0001")
            self.assertEqual(found.parent.name, "open")
            self.assertEqual(found.read_bytes(), original_bytes)
            stderr_val = err.getvalue()
            self.assertIn("refused", stderr_val)
            self.assertIn("hand the gate to a plan", stderr_val)
            self.assertIn("cite satisfying evidence", stderr_val)
            self.assertIn("explicitly release the gate first", stderr_val)

    def test_ungated_close_refusal_positional_spelling(self) -> None:
        """Positional spelling refuses illegitimate close of release-gated item."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = _setup_repo(Path(tmp))
            item_path = _create_item(
                repo, status="open", work_kind="bug", blocks_release="next"
            )
            original_bytes = item_path.read_bytes()

            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                rc = cli.main(
                    [
                        "backlog",
                        "set",
                        "done",
                        "bk0001",
                        "--yes",
                        "--no-commit",
                        "--dir",
                        str(repo),
                    ]
                )
            self.assertEqual(rc, 1)
            found = _find_item(repo, "bk0001")
            self.assertEqual(found.parent.name, "open")
            self.assertEqual(found.read_bytes(), original_bytes)
            stderr_val = err.getvalue()
            self.assertIn("refused", stderr_val)
            self.assertIn("hand the gate to a plan", stderr_val)
            self.assertIn("cite satisfying evidence", stderr_val)
            self.assertIn("explicitly release the gate first", stderr_val)

    # =========================================================================
    # V-01 / E-01: Gated -> parked warning
    # =========================================================================

    def test_gated_to_parked_warning_status_spelling(self) -> None:
        """Status spelling allows gated -> parked transition with warning on stderr."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = _setup_repo(Path(tmp))
            item_path = _create_item(
                repo, status="open", work_kind="bug", blocks_release="next"
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
                        "--yes",
                        "--no-commit",
                        "--dir",
                        str(repo),
                    ]
                )
            self.assertEqual(rc, 0)
            found = _find_item(repo, "bk0001")
            self.assertEqual(found.parent.name, "parked")
            self.assertIn("warning:", err.getvalue())
            self.assertIn("parking a release-blocking item hides gate", err.getvalue())

    def test_gated_to_parked_warning_positional_spelling(self) -> None:
        """Positional spelling allows gated -> parked transition with warning on stderr."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = _setup_repo(Path(tmp))
            _create_item(repo, status="open", work_kind="bug", blocks_release="next")

            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                rc = cli.main(
                    [
                        "backlog",
                        "set",
                        "parked",
                        "bk0001",
                        "--yes",
                        "--no-commit",
                        "--dir",
                        str(repo),
                    ]
                )
            self.assertEqual(rc, 0)
            found = _find_item(repo, "bk0001")
            self.assertEqual(found.parent.name, "parked")
            self.assertIn("warning:", err.getvalue())
            self.assertIn("parking a release-blocking item hides gate", err.getvalue())

    # =========================================================================
    # V-01 / F-05: Dry-run refusal parity on illegitimate close
    # =========================================================================

    def test_dry_run_refuses_illegitimate_close_status_spelling(self) -> None:
        """Status spelling --dry-run on illegitimate close exits 1."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = _setup_repo(Path(tmp))
            item_path = _create_item(
                repo, status="open", work_kind="bug", blocks_release="next"
            )
            original_bytes = item_path.read_bytes()

            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                rc = cli.main(
                    [
                        "backlog",
                        "set",
                        str(item_path),
                        "--status",
                        "done",
                        "--dry-run",
                        "--yes",
                        "--no-commit",
                        "--dir",
                        str(repo),
                    ]
                )
            self.assertEqual(rc, 1)
            found = _find_item(repo, "bk0001")
            self.assertEqual(found.parent.name, "open")
            self.assertEqual(found.read_bytes(), original_bytes)

    def test_dry_run_refuses_illegitimate_close_positional_spelling(self) -> None:
        """Positional spelling --dry-run on illegitimate close exits 1 (F-05 parity)."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = _setup_repo(Path(tmp))
            item_path = _create_item(
                repo, status="open", work_kind="bug", blocks_release="next"
            )
            original_bytes = item_path.read_bytes()

            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                rc = cli.main(
                    [
                        "backlog",
                        "set",
                        "done",
                        "bk0001",
                        "--dry-run",
                        "--yes",
                        "--no-commit",
                        "--dir",
                        str(repo),
                    ]
                )
            self.assertEqual(rc, 1)
            found = _find_item(repo, "bk0001")
            self.assertEqual(found.parent.name, "open")
            self.assertEqual(found.read_bytes(), original_bytes)

    # =========================================================================
    # V-02 / E-02: Same-call `--blocks-release -` DE-GATED success
    # =========================================================================

    def test_same_call_degate_to_done_status_spelling(self) -> None:
        """Status spelling closes done with same-call --blocks-release - (DE-GATED path)."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = _setup_repo(Path(tmp))
            item_path = _create_item(
                repo, status="open", work_kind="bug", blocks_release="next"
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
                        "--blocks-release",
                        "-",
                        "--yes",
                        "--no-commit",
                        "--dir",
                        str(repo),
                    ]
                )
            self.assertEqual(rc, 0)
            found = _find_item(repo, "bk0001")
            self.assertEqual(found.parent.name, "done")
            self.assertNotIn("- Blocks-Release:", found.read_text(encoding="utf-8"))

    def test_same_call_degate_to_done_positional_spelling(self) -> None:
        """Positional spelling closes done with same-call --blocks-release - (DE-GATED path)."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = _setup_repo(Path(tmp))
            _create_item(repo, status="open", work_kind="bug", blocks_release="next")

            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                rc = cli.main(
                    [
                        "backlog",
                        "set",
                        "done",
                        "bk0001",
                        "--blocks-release",
                        "-",
                        "--yes",
                        "--no-commit",
                        "--dir",
                        str(repo),
                    ]
                )
            self.assertEqual(rc, 0)
            found = _find_item(repo, "bk0001")
            self.assertEqual(found.parent.name, "done")
            self.assertNotIn("- Blocks-Release:", found.read_text(encoding="utf-8"))

    # =========================================================================
    # V-02 / E-02: Negative fence: ungated chore closes done at exit 0
    # =========================================================================

    def test_ungated_chore_closes_done_status_spelling(self) -> None:
        """Status spelling closes ungated chore item without gate interaction."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = _setup_repo(Path(tmp))
            item_path = _create_item(
                repo, status="open", work_kind="chore", blocks_release=None
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
                        "--yes",
                        "--no-commit",
                        "--dir",
                        str(repo),
                    ]
                )
            self.assertEqual(rc, 0)
            found = _find_item(repo, "bk0001")
            self.assertEqual(found.parent.name, "done")
            self.assertNotIn("- Blocks-Release:", found.read_text(encoding="utf-8"))

    def test_ungated_chore_closes_done_positional_spelling(self) -> None:
        """Positional spelling closes ungated chore item without gate interaction."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = _setup_repo(Path(tmp))
            _create_item(repo, status="open", work_kind="chore", blocks_release=None)

            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                rc = cli.main(
                    [
                        "backlog",
                        "set",
                        "done",
                        "bk0001",
                        "--yes",
                        "--no-commit",
                        "--dir",
                        str(repo),
                    ]
                )
            self.assertEqual(rc, 0)
            found = _find_item(repo, "bk0001")
            self.assertEqual(found.parent.name, "done")
            self.assertNotIn("- Blocks-Release:", found.read_text(encoding="utf-8"))

    # =========================================================================
    # V-02 / E-02: Gate-default interaction on live transition
    # =========================================================================

    def test_gate_default_interaction_status_spelling(self) -> None:
        """Status spelling judges priority demote against defaulted gate."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = _setup_repo(Path(tmp))
            item_path = _create_item(
                repo,
                status="open",
                work_kind="bug",
                priority="high",
                blocks_release=None,
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
                        "--priority",
                        "low",
                        "--yes",
                        "--no-commit",
                        "--dir",
                        str(repo),
                    ]
                )
            self.assertEqual(rc, 0)
            found = _find_item(repo, "bk0001")
            content = found.read_text(encoding="utf-8")
            self.assertIn("- Blocks-Release: next", content)
            self.assertIn("demoting the priority", err.getvalue())

    def test_gate_default_interaction_positional_spelling(self) -> None:
        """Positional spelling judges priority demote against defaulted gate."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = _setup_repo(Path(tmp))
            _create_item(
                repo,
                status="open",
                work_kind="bug",
                priority="high",
                blocks_release=None,
            )

            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                rc = cli.main(
                    [
                        "backlog",
                        "set",
                        "open",
                        "bk0001",
                        "--priority",
                        "low",
                        "--yes",
                        "--no-commit",
                        "--dir",
                        str(repo),
                    ]
                )
            self.assertEqual(rc, 0)
            found = _find_item(repo, "bk0001")
            content = found.read_text(encoding="utf-8")
            self.assertIn("- Blocks-Release: next", content)
            self.assertIn("demoting the priority", err.getvalue())

    # =========================================================================
    # V-03 / E-03: Evidence SATISFIED success (gate preserved)
    # =========================================================================

    def test_evidence_satisfied_success_status_spelling(self) -> None:
        """Status spelling closes done with valid in-tree evidence, preserving gate."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = _setup_repo(Path(tmp))
            item_path = _create_item(
                repo, status="open", work_kind="bug", blocks_release="next"
            )
            ev_path = repo / ".aw" / "records" / "reviews" / "20260901-test.review.md"
            ev_path.parent.mkdir(parents=True, exist_ok=True)
            ev_path.write_text("# Review evidence\n", encoding="utf-8")

            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                rc = cli.main(
                    [
                        "backlog",
                        "set",
                        str(item_path),
                        "--status",
                        "done",
                        "--evidence",
                        str(ev_path),
                        "--yes",
                        "--no-commit",
                        "--dir",
                        str(repo),
                    ]
                )
            self.assertEqual(rc, 0)
            found = _find_item(repo, "bk0001")
            self.assertEqual(found.parent.name, "done")
            self.assertIn("- Blocks-Release: next", found.read_text(encoding="utf-8"))

    def test_evidence_satisfied_success_positional_spelling(self) -> None:
        """Positional spelling closes done with valid in-tree evidence, preserving gate."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = _setup_repo(Path(tmp))
            _create_item(repo, status="open", work_kind="bug", blocks_release="next")
            ev_path = repo / ".aw" / "records" / "reviews" / "20260901-test.review.md"
            ev_path.parent.mkdir(parents=True, exist_ok=True)
            ev_path.write_text("# Review evidence\n", encoding="utf-8")

            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                rc = cli.main(
                    [
                        "backlog",
                        "set",
                        "done",
                        "bk0001",
                        "--evidence",
                        str(ev_path),
                        "--yes",
                        "--no-commit",
                        "--dir",
                        str(repo),
                    ]
                )
            self.assertEqual(rc, 0)
            found = _find_item(repo, "bk0001")
            self.assertEqual(found.parent.name, "done")
            self.assertIn("- Blocks-Release: next", found.read_text(encoding="utf-8"))

    # =========================================================================
    # V-03 / E-03: Evidence unresolvable refusal
    # =========================================================================

    def test_evidence_unresolvable_refusal_status_spelling(self) -> None:
        """Status spelling refuses close when evidence cannot be resolved."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = _setup_repo(Path(tmp))
            item_path = _create_item(
                repo, status="open", work_kind="bug", blocks_release="next"
            )
            original_bytes = item_path.read_bytes()

            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                rc = cli.main(
                    [
                        "backlog",
                        "set",
                        str(item_path),
                        "--status",
                        "done",
                        "--evidence",
                        "nope/absent.md",
                        "--yes",
                        "--no-commit",
                        "--dir",
                        str(repo),
                    ]
                )
            self.assertEqual(rc, 1)
            found = _find_item(repo, "bk0001")
            self.assertEqual(found.parent.name, "open")
            self.assertEqual(found.read_bytes(), original_bytes)
            self.assertIn("refused", err.getvalue())

    def test_evidence_unresolvable_refusal_positional_spelling(self) -> None:
        """Positional spelling refuses close when evidence cannot be resolved."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = _setup_repo(Path(tmp))
            item_path = _create_item(
                repo, status="open", work_kind="bug", blocks_release="next"
            )
            original_bytes = item_path.read_bytes()

            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                rc = cli.main(
                    [
                        "backlog",
                        "set",
                        "done",
                        "bk0001",
                        "--evidence",
                        "nope/absent.md",
                        "--yes",
                        "--no-commit",
                        "--dir",
                        str(repo),
                    ]
                )
            self.assertEqual(rc, 1)
            found = _find_item(repo, "bk0001")
            self.assertEqual(found.parent.name, "open")
            self.assertEqual(found.read_bytes(), original_bytes)
            self.assertIn("refused", err.getvalue())

    # =========================================================================
    # V-03 / E-03: Priority-demote warning on positional spelling
    # =========================================================================

    def test_priority_demote_warning_status_spelling(self) -> None:
        """Status spelling warns when demoting priority of a release blocker."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = _setup_repo(Path(tmp))
            item_path = _create_item(
                repo,
                status="open",
                work_kind="bug",
                priority="high",
                blocks_release="next",
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
                        "--priority",
                        "low",
                        "--yes",
                        "--no-commit",
                        "--dir",
                        str(repo),
                    ]
                )
            self.assertEqual(rc, 0)
            self.assertIn("warning:", err.getvalue())
            self.assertIn("demoting the priority", err.getvalue())

    def test_priority_demote_warning_positional_spelling(self) -> None:
        """Positional spelling warns when demoting priority of a release blocker."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = _setup_repo(Path(tmp))
            _create_item(
                repo,
                status="open",
                work_kind="bug",
                priority="high",
                blocks_release="next",
            )

            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                rc = cli.main(
                    [
                        "backlog",
                        "set",
                        "open",
                        "bk0001",
                        "--priority",
                        "low",
                        "--yes",
                        "--no-commit",
                        "--dir",
                        str(repo),
                    ]
                )
            self.assertEqual(rc, 0)
            self.assertIn("warning:", err.getvalue())
            self.assertIn("demoting the priority", err.getvalue())

    # =========================================================================
    # F-06 / E-07: Untyped aw set done <id6> refusal
    # =========================================================================

    def test_untyped_set_done_refusal(self) -> None:
        """Untyped aw set done <id6> also refuses close of release blocker."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = _setup_repo(Path(tmp))
            item_path = _create_item(
                repo, status="open", work_kind="bug", blocks_release="next"
            )
            original_bytes = item_path.read_bytes()

            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                rc = cli.main(
                    [
                        "set",
                        "done",
                        "bk0001",
                        "--yes",
                        "--no-commit",
                        "--dir",
                        str(repo),
                    ]
                )
            self.assertEqual(rc, 1)
            found = _find_item(repo, "bk0001")
            self.assertEqual(found.parent.name, "open")
            self.assertEqual(found.read_bytes(), original_bytes)
            self.assertIn("refused", err.getvalue())
