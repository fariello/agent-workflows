"""Regression tests pinning the backlog transition authority ruling by outcome.

Per decision D161 (plan tm8k2n), no backlog status transition requires an authority
attestation (such as --by-human). This module tests observable outcomes: every backlog
transition that production automation performs succeeds at exit 0 with no attestation
flag supplied, on both setter spellings, and relocates the file.

Tested by outcome, never by code structure (no inspect, ast, regex, or caller counting).
"""

from __future__ import annotations

import io
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
import tempfile
import unittest

from agent_workflows import cli
from tests.record_builder import RecordBuilder, assert_field


def _setup_repo(root: Path) -> Path:
    """Create minimal repository structure with backlog and plan directories."""
    for sub in ("open", "parked", "graduated", "done", "blocked"):
        (root / ".aw" / "records" / "backlog" / sub).mkdir(parents=True, exist_ok=True)
    for sub in ("pending", "executed"):
        (root / ".aw" / "records" / "plans" / sub).mkdir(parents=True, exist_ok=True)
    (root / ".aw" / "records" / "releases").mkdir(parents=True, exist_ok=True)
    (root / ".aw" / "config").mkdir(parents=True, exist_ok=True)
    (root / ".aw" / "config" / "config.json").write_text("{}", encoding="utf-8")
    return root


def _create_item(
    repo: Path,
    *,
    status: str,
    work_kind: str = "chore",
    item_id: str = "bk0001",
    blocks_release: str | None = None,
) -> Path:
    """Create a backlog item with valid metadata."""
    extra: dict[str, str] = {}
    if blocks_release is not None:
        extra["blocks_release"] = blocks_release
    p = (
        repo
        / ".aw"
        / "records"
        / "backlog"
        / status
        / f"20261007-{item_id}-01-{item_id}-test.backlog.md"
    )
    p.write_text(
        RecordBuilder().backlog(
            id6=item_id,
            status=status,
            set=item_id,
            priority="low",
            work_kind=work_kind,
            summary=f"Test defect {item_id}",
            when="2026-10-07",
            history=[f"- 2026-10-07 created (tester): Test defect {item_id}"],
            text_only=True,
            **extra,
        ),
        encoding="utf-8",
    )
    return p


def _write_conforming_plan(
    repo: Path,
    *,
    id6: str = "pl0001",
    backlog_id6: str = "bk0001",
    set_id: str = "demo",
    status: str = "to-review",
) -> Path:
    """Write a fully-conforming plan citing the backlog item."""
    target_dir = "executed" if status == "executed" else "pending"
    plan_dir = repo / ".aw" / "records" / "plans" / target_dir
    plan_dir.mkdir(parents=True, exist_ok=True)
    p = plan_dir / f"20260901-{set_id}-01-{id6}-plan.ipd.md"
    exec_state = "performed" if status == "executed" else "pending"
    val_result = "pass" if status == "executed" else "pending"
    plan_body = (
        f"## Goal\n\nGoal {id6}.\n\n"
        "## Detailed Implementation Checklist (TODO)\n\n"
        "### Task group 1: work\n\n"
        "- [ ] E-01 Work item\n"
        "  - Depends on: none\n"
        "  - Expected outcome: done\n"
        f"  - Execution state: {exec_state}\n\n"
        "## Project conventions discovered (Step 0)\n\n"
        "None.\n\n"
        "## Findings\n\n"
        "None.\n\n"
        "## Proposed changes (ordered, validatable)\n\n"
        "1. E-01 do work.\n\n"
        "## Deferred / out of scope (with reason)\n\n"
        "- None.\n\n"
        "## Scope check\n\n"
        "- None.\n\n"
        "## Required tests / validation\n\n"
        "- None.\n\n"
        "## Spec / documentation sync\n\n"
        "- None.\n\n"
        "## Open questions\n\n"
        "- None.\n\n"
        "## Validation and cross-check (verify before reporting done)\n\n"
        "- [ ] V-01 validates E-01\n"
        "  - Required evidence: check.\n"
        "  - Observed evidence:\n"
        f"  - Result: {val_result}\n\n"
        "## Approval and execution gate\n\n"
        "- Size assessment: standard\n"
        "- Cohesion rationale: not required\n"
    )
    p.write_text(
        RecordBuilder().plan(
            id6=id6,
            title=f"Plan {id6}",
            when="2026-09-01",
            status=status,
            work_kind="chore",
            priority="medium",
            set=set_id,
            order=1,
            from_backlog=backlog_id6,
            scope_paths="README.md",
            highest_e_allocated="01",
            author="test",
            item_dependencies="none",
            history=[f"- 2026-09-01 {status} (test): created"],
            body=plan_body,
            raw_fields={
                "Concern": "Test concern.",
                "Scope": "Test scope.",
            },
            text_only=True,
        ),
        encoding="utf-8",
    )
    return p


def _find_item(repo: Path, item_id: str) -> Path:
    """Locate the item file regardless of which status directory it moved into."""
    matches = list(
        (repo / ".aw" / "records" / "backlog").rglob(f"*{item_id}*.backlog.md")
    )
    assert matches, f"Could not find item {item_id} in {repo}"
    return matches[0]


class TestBacklogTransitionAuthority(unittest.TestCase):
    """Pin by observable outcome that automation-performed backlog transitions require no attestation."""

    # -------------------------------------------------------------------------
    # Target: graduated
    # Production site: runner_shared._execute_plan_turn (lines 36969-36981)
    # builds: ["backlog", "set", item["id6"], "--status", "graduated", ...]
    # -------------------------------------------------------------------------

    def test_graduated_target_status_spelling_succeeds_without_attestation(
        self,
    ) -> None:
        """Target graduated: flag spelling succeeds without attestation (runner_shared._execute_plan_turn)."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = _setup_repo(Path(tmp))
            item_path = _create_item(repo, status="open", item_id="bk0001")
            _write_conforming_plan(
                repo, id6="pl0001", backlog_id6="bk0001", status="to-review"
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
                        "--message",
                        "graduated by test",
                        "--no-commit",
                        "--dir",
                        str(repo),
                    ]
                )
            self.assertEqual(rc, 0, f"Command failed: {err.getvalue()}")
            relocated = _find_item(repo, "bk0001")
            self.assertEqual(relocated.parent.name, "graduated")
            assert_field(relocated, "status", "graduated")

    def test_graduated_target_positional_spelling_succeeds_without_attestation(
        self,
    ) -> None:
        """Target graduated: positional spelling succeeds without attestation (runner_shared._execute_plan_turn)."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = _setup_repo(Path(tmp))
            _create_item(repo, status="open", item_id="bk0001")
            _write_conforming_plan(
                repo, id6="pl0001", backlog_id6="bk0001", status="to-review"
            )

            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                rc = cli.main(
                    [
                        "backlog",
                        "set",
                        "graduated",
                        "bk0001",
                        "--message",
                        "graduated by test",
                        "--yes",
                        "--no-commit",
                        "--dir",
                        str(repo),
                    ]
                )
            self.assertEqual(rc, 0, f"Command failed: {err.getvalue()}")
            relocated = _find_item(repo, "bk0001")
            self.assertEqual(relocated.parent.name, "graduated")
            assert_field(relocated, "status", "graduated")

    # -------------------------------------------------------------------------
    # Target: open (containment rollback and corrective reopen)
    # Production site: runner_shared._execute_plan_turn (lines 37059-37070)
    # builds: ["backlog", "set", item["id6"], "--status", "open", ...]
    # -------------------------------------------------------------------------

    def test_open_target_rollback_status_spelling_succeeds_without_attestation(
        self,
    ) -> None:
        """Target open: containment rollback on flag spelling succeeds without attestation (runner_shared._execute_plan_turn)."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = _setup_repo(Path(tmp))
            item_path = _create_item(repo, status="graduated", item_id="bk0001")

            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                rc = cli.main(
                    [
                        "backlog",
                        "set",
                        str(item_path),
                        "--status",
                        "open",
                        "--message",
                        "handoff incomplete: TEST-ROLLBACK",
                        "--no-commit",
                        "--dir",
                        str(repo),
                    ]
                )
            self.assertEqual(rc, 0, f"Command failed: {err.getvalue()}")
            relocated = _find_item(repo, "bk0001")
            self.assertEqual(relocated.parent.name, "open")
            assert_field(relocated, "status", "open")

    def test_open_target_rollback_positional_spelling_succeeds_without_attestation(
        self,
    ) -> None:
        """Target open: containment rollback on positional spelling succeeds without attestation (runner_shared._execute_plan_turn)."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = _setup_repo(Path(tmp))
            _create_item(repo, status="graduated", item_id="bk0001")

            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                rc = cli.main(
                    [
                        "backlog",
                        "set",
                        "open",
                        "bk0001",
                        "--message",
                        "handoff incomplete: TEST-ROLLBACK",
                        "--yes",
                        "--no-commit",
                        "--dir",
                        str(repo),
                    ]
                )
            self.assertEqual(rc, 0, f"Command failed: {err.getvalue()}")
            relocated = _find_item(repo, "bk0001")
            self.assertEqual(relocated.parent.name, "open")
            assert_field(relocated, "status", "open")

    def test_open_target_reopen_status_spelling_succeeds_without_attestation(
        self,
    ) -> None:
        """Target open: corrective done -> open on flag spelling succeeds without attestation (runner recovery)."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = _setup_repo(Path(tmp))
            item_path = _create_item(repo, status="done", item_id="bk0001")

            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                rc = cli.main(
                    [
                        "backlog",
                        "set",
                        str(item_path),
                        "--status",
                        "open",
                        "--message",
                        "corrective reopen",
                        "--no-commit",
                        "--dir",
                        str(repo),
                    ]
                )
            self.assertEqual(rc, 0, f"Command failed: {err.getvalue()}")
            relocated = _find_item(repo, "bk0001")
            self.assertEqual(relocated.parent.name, "open")
            assert_field(relocated, "status", "open")

    def test_open_target_reopen_positional_spelling_succeeds_without_attestation(
        self,
    ) -> None:
        """Target open: corrective done -> open on positional spelling succeeds without attestation (runner recovery)."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = _setup_repo(Path(tmp))
            _create_item(repo, status="done", item_id="bk0001")

            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                rc = cli.main(
                    [
                        "backlog",
                        "set",
                        "open",
                        "bk0001",
                        "--message",
                        "corrective reopen",
                        "--yes",
                        "--no-commit",
                        "--dir",
                        str(repo),
                    ]
                )
            self.assertEqual(rc, 0, f"Command failed: {err.getvalue()}")
            relocated = _find_item(repo, "bk0001")
            self.assertEqual(relocated.parent.name, "open")
            assert_field(relocated, "status", "open")

    # -------------------------------------------------------------------------
    # Target: done (automated backlog close)
    # Production site: runner_shared.close_backlog_item (lines 38250-38269)
    # reached via: oc_runipd.process_backlog_close, agy_runipd.process_backlog_close,
    # and runner_shared.perform_coordinator_backlog_close
    # builds: ["backlog", "set", item_id6, "--status", "done", ...]
    # -------------------------------------------------------------------------

    def test_done_target_status_spelling_succeeds_without_attestation(self) -> None:
        """Target done: automated close on flag spelling succeeds without attestation (runner_shared.close_backlog_item)."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = _setup_repo(Path(tmp))
            item_path = _create_item(repo, status="graduated", item_id="bk0001")
            # Conforming executed carrier satisfies close predicate
            _write_conforming_plan(
                repo, id6="pl0001", backlog_id6="bk0001", status="executed"
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
                        "--message",
                        "closed done by runner",
                        "--no-commit",
                        "--dir",
                        str(repo),
                    ]
                )
            self.assertEqual(rc, 0, f"Command failed: {err.getvalue()}")
            relocated = _find_item(repo, "bk0001")
            self.assertEqual(relocated.parent.name, "done")
            assert_field(relocated, "status", "done")

    def test_done_target_positional_spelling_succeeds_without_attestation(self) -> None:
        """Target done: automated close on positional spelling succeeds without attestation (runner_shared.close_backlog_item)."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = _setup_repo(Path(tmp))
            _create_item(repo, status="graduated", item_id="bk0001")
            # Conforming executed carrier satisfies close predicate
            _write_conforming_plan(
                repo, id6="pl0001", backlog_id6="bk0001", status="executed"
            )

            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                rc = cli.main(
                    [
                        "backlog",
                        "set",
                        "done",
                        "bk0001",
                        "--message",
                        "closed done by runner",
                        "--yes",
                        "--no-commit",
                        "--dir",
                        str(repo),
                    ]
                )
            self.assertEqual(rc, 0, f"Command failed: {err.getvalue()}")
            relocated = _find_item(repo, "bk0001")
            self.assertEqual(relocated.parent.name, "done")
            assert_field(relocated, "status", "done")
