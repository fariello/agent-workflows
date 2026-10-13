"""Tests for IPD ncmugb: Require an executed plan when a backlog close cites a plan as SATISFIED evidence.

Pins:
- E-01 / V-01:
  (a) evidence = a plan in plans/pending/ with - Status: to-review: REFUSED on
      aw backlog set <id> --status done --evidence ... AND on aw backlog set done <id> --evidence ...
  (b) draft pending plan, not-executed plan, superseded plan refused at predicate level
  (c) --dry-run with a pending-plan citation refuses (rc 1)
  (d) evidence = a plan in plans/executed/ accepted on both spellings with - Close-Evidence: written
  (e) evidence = sharded plans/executed/YYYYMM/ and legacy .agents/plans/executed/ accepted
  (f) non-plan records artifacts (review, release) accepted unchanged
  (g) AT REST: item citing pending plan produces check.blocking-item-closed-without-gate; citing executed plan clean
  (h) refusal reason names cited path and phrase 'has not shipped', item file byte-identical
"""

from __future__ import annotations

import io
import subprocess
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
    status: str = "open",
    work_kind: str = "bug",
    item_id: str = "bk0001",
    priority: str = "medium",
    blocks_release: str | None = "next",
    close_evidence: str | None = None,
    history_date: str = "2026-10-05",
) -> Path:
    """Create a backlog item in the given status."""
    lines = [
        f"- Id: {item_id}",
        f"- Status: {status}",
    ]
    if blocks_release is not None:
        lines.append(f"- Blocks-Release: {blocks_release}")
    if close_evidence is not None:
        lines.append(f"- Close-Evidence: {close_evidence}")
    lines.extend(
        [
            f"- Set: {item_id}",
            f"- Priority: {priority}",
            f"- Work-Kind: {work_kind}",
            "- Summary: Test defect",
            "",
            "## Workflow history",
            f"- {history_date} created (tester): initial",
        ]
    )
    if status == "done":
        lines.append(f"- {history_date} closed (tester): done")
    lines.append("")
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


def _create_plan(
    repo: Path,
    *,
    bucket: str,
    plan_id: str,
    status: str = "approved",
    base: str = ".aw/records/plans",
) -> Path:
    """Create a real .ipd.md plan fixture with - Id: and - Status: in the named bucket."""
    plan_dir = repo / base / bucket
    plan_dir.mkdir(parents=True, exist_ok=True)
    p = plan_dir / f"20261011-test01-01-{plan_id}-test.ipd.md"
    content = (
        f"# IPD: Test plan {plan_id}\n\n"
        f"- Id: {plan_id}\n"
        f"- Status: {status}\n"
        "- Set: test01\n"
        "- Order: 1\n"
        "- Scope: test\n"
    )
    p.write_text(content, encoding="utf-8")
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


class TestBacklogCloseEvidencePlanDisposition(unittest.TestCase):
    """Pin SATISFIED evidence plan disposition requirements (IPD ncmugb)."""

    # =========================================================================
    # Case (a): pending plan with to-review status refused on both spellings
    # =========================================================================

    def test_case_a_pending_plan_refused_status_spelling(self) -> None:
        """Status spelling refuses close when citing a pending to-review plan."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = _setup_repo(Path(tmp))
            item_path = _create_item(
                repo, status="open", work_kind="bug", blocks_release="next"
            )
            plan_path = _create_plan(
                repo, bucket="pending", plan_id="plnpnd", status="to-review"
            )
            rel_plan = str(plan_path.relative_to(repo)).replace("\\", "/")

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
                        rel_plan,
                        "--yes",
                        "--no-commit",
                        "--dir",
                        str(repo),
                    ]
                )
            self.assertEqual(rc, 1)
            found = _find_item(repo, "bk0001")
            self.assertEqual(found.parent.name, "open")

            verdict = check_engine.evaluate_blocking_close(
                repo, item_path, "done", evidence=rel_plan
            )
            self.assertFalse(verdict.legitimate)
            self.assertIsNone(verdict.path)

    def test_case_a_pending_plan_refused_positional_spelling(self) -> None:
        """Positional spelling refuses close when citing a pending to-review plan."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = _setup_repo(Path(tmp))
            item_path = _create_item(
                repo, status="open", work_kind="bug", blocks_release="next"
            )
            plan_path = _create_plan(
                repo, bucket="pending", plan_id="plnpnd", status="to-review"
            )
            rel_plan = str(plan_path.relative_to(repo)).replace("\\", "/")

            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                rc = cli.main(
                    [
                        "backlog",
                        "set",
                        "done",
                        "bk0001",
                        "--evidence",
                        rel_plan,
                        "--yes",
                        "--no-commit",
                        "--dir",
                        str(repo),
                    ]
                )
            self.assertEqual(rc, 1)
            found = _find_item(repo, "bk0001")
            self.assertEqual(found.parent.name, "open")

            verdict = check_engine.evaluate_blocking_close(
                repo, item_path, "done", evidence=rel_plan
            )
            self.assertFalse(verdict.legitimate)
            self.assertIsNone(verdict.path)

    # =========================================================================
    # Case (b): draft pending, not-executed, and superseded plans refused at predicate
    # =========================================================================

    def test_case_b_draft_pending_plan_refused_predicate(self) -> None:
        """Predicate refuses close citing a draft pending plan."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = _setup_repo(Path(tmp))
            item_path = _create_item(
                repo, status="open", work_kind="bug", blocks_release="next"
            )
            plan_path = _create_plan(
                repo, bucket="pending", plan_id="plndrf", status="draft"
            )
            rel_plan = str(plan_path.relative_to(repo)).replace("\\", "/")

            verdict = check_engine.evaluate_blocking_close(
                repo, item_path, "done", evidence=rel_plan
            )
            self.assertFalse(verdict.legitimate)
            self.assertIsNone(verdict.path)

    def test_case_b_not_executed_plan_refused_predicate(self) -> None:
        """Predicate refuses close citing a plan in plans/not-executed/."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = _setup_repo(Path(tmp))
            item_path = _create_item(
                repo, status="open", work_kind="bug", blocks_release="next"
            )
            plan_path = _create_plan(
                repo, bucket="not-executed", plan_id="plnnot", status="not-executed"
            )
            rel_plan = str(plan_path.relative_to(repo)).replace("\\", "/")

            verdict = check_engine.evaluate_blocking_close(
                repo, item_path, "done", evidence=rel_plan
            )
            self.assertFalse(verdict.legitimate)
            self.assertIsNone(verdict.path)

    def test_case_b_superseded_plan_refused_predicate(self) -> None:
        """Predicate refuses close citing a plan in plans/superseded/."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = _setup_repo(Path(tmp))
            item_path = _create_item(
                repo, status="open", work_kind="bug", blocks_release="next"
            )
            plan_path = _create_plan(
                repo, bucket="superseded", plan_id="plnsup", status="superseded"
            )
            rel_plan = str(plan_path.relative_to(repo)).replace("\\", "/")

            verdict = check_engine.evaluate_blocking_close(
                repo, item_path, "done", evidence=rel_plan
            )
            self.assertFalse(verdict.legitimate)
            self.assertIsNone(verdict.path)

    # =========================================================================
    # Case (c): --dry-run with pending-plan citation refuses (rc 1)
    # =========================================================================

    def test_case_c_dry_run_pending_plan_refused(self) -> None:
        """--dry-run refuses close citing a pending plan with exit code 1."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = _setup_repo(Path(tmp))
            _create_item(repo, status="open", work_kind="bug", blocks_release="next")
            plan_path = _create_plan(
                repo, bucket="pending", plan_id="plnpnd", status="to-review"
            )
            rel_plan = str(plan_path.relative_to(repo)).replace("\\", "/")

            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                rc = cli.main(
                    [
                        "backlog",
                        "set",
                        "done",
                        "bk0001",
                        "--evidence",
                        rel_plan,
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

    # =========================================================================
    # Case (d): executed plan accepted on both spellings with - Close-Evidence:
    # =========================================================================

    def test_case_d_executed_plan_accepted_status_spelling(self) -> None:
        """Status spelling accepts close citing an executed plan."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = _setup_repo(Path(tmp))
            item_path = _create_item(
                repo, status="open", work_kind="bug", blocks_release="next"
            )
            plan_path = _create_plan(
                repo, bucket="executed", plan_id="plnexc", status="executed"
            )
            rel_plan = str(plan_path.relative_to(repo)).replace("\\", "/")

            verdict = check_engine.evaluate_blocking_close(
                repo, item_path, "done", evidence=rel_plan
            )
            self.assertTrue(verdict.legitimate)
            self.assertEqual(verdict.path, "SATISFIED")

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
                        rel_plan,
                        "--yes",
                        "--no-commit",
                        "--dir",
                        str(repo),
                    ]
                )
            self.assertEqual(rc, 0)
            found = _find_item(repo, "bk0001")
            self.assertEqual(found.parent.name, "done")
            content = found.read_text(encoding="utf-8")
            self.assertIn(f"- Close-Evidence: {rel_plan}", content)

    def test_case_d_executed_plan_accepted_positional_spelling(self) -> None:
        """Positional spelling accepts close citing an executed plan."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = _setup_repo(Path(tmp))
            item_path = _create_item(
                repo, status="open", work_kind="bug", blocks_release="next"
            )
            plan_path = _create_plan(
                repo, bucket="executed", plan_id="plnexc", status="executed"
            )
            rel_plan = str(plan_path.relative_to(repo)).replace("\\", "/")

            verdict = check_engine.evaluate_blocking_close(
                repo, item_path, "done", evidence=rel_plan
            )
            self.assertTrue(verdict.legitimate)
            self.assertEqual(verdict.path, "SATISFIED")

            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                rc = cli.main(
                    [
                        "backlog",
                        "set",
                        "done",
                        "bk0001",
                        "--evidence",
                        rel_plan,
                        "--yes",
                        "--no-commit",
                        "--dir",
                        str(repo),
                    ]
                )
            self.assertEqual(rc, 0)
            found = _find_item(repo, "bk0001")
            self.assertEqual(found.parent.name, "done")
            content = found.read_text(encoding="utf-8")
            self.assertIn(f"- Close-Evidence: {rel_plan}", content)

    # =========================================================================
    # Case (e): sharded executed and legacy .agents executed plans accepted
    # =========================================================================

    def test_case_e_sharded_executed_plan_accepted(self) -> None:
        """Sharded plans/executed/YYYYMM/ plan is accepted as close evidence."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = _setup_repo(Path(tmp))
            item_path = _create_item(
                repo, status="open", work_kind="bug", blocks_release="next"
            )
            plan_path = _create_plan(
                repo, bucket="executed/202610", plan_id="plnshd", status="executed"
            )
            rel_plan = str(plan_path.relative_to(repo)).replace("\\", "/")

            verdict = check_engine.evaluate_blocking_close(
                repo, item_path, "done", evidence=rel_plan
            )
            self.assertTrue(verdict.legitimate)
            self.assertEqual(verdict.path, "SATISFIED")

            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                rc = cli.main(
                    [
                        "backlog",
                        "set",
                        "done",
                        "bk0001",
                        "--evidence",
                        rel_plan,
                        "--yes",
                        "--no-commit",
                        "--dir",
                        str(repo),
                    ]
                )
            self.assertEqual(rc, 0)
            found = _find_item(repo, "bk0001")
            self.assertEqual(found.parent.name, "done")

    def test_case_e_legacy_agents_executed_plan_accepted(self) -> None:
        """Legacy .agents/plans/executed/ plan is accepted as close evidence."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = _setup_repo(Path(tmp))
            item_path = _create_item(
                repo, status="open", work_kind="bug", blocks_release="next"
            )
            plan_path = _create_plan(
                repo,
                bucket="executed",
                plan_id="plnleg",
                status="executed",
                base=".agents/plans",
            )
            rel_plan = str(plan_path.relative_to(repo)).replace("\\", "/")

            verdict = check_engine.evaluate_blocking_close(
                repo, item_path, "done", evidence=rel_plan
            )
            self.assertTrue(verdict.legitimate)
            self.assertEqual(verdict.path, "SATISFIED")

            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                rc = cli.main(
                    [
                        "backlog",
                        "set",
                        "done",
                        "bk0001",
                        "--evidence",
                        rel_plan,
                        "--yes",
                        "--no-commit",
                        "--dir",
                        str(repo),
                    ]
                )
            self.assertEqual(rc, 0)
            found = _find_item(repo, "bk0001")
            self.assertEqual(found.parent.name, "done")

    # =========================================================================
    # Case (f): non-plan records artifacts accepted unchanged
    # =========================================================================

    def test_case_f_review_artifact_accepted(self) -> None:
        """A review records artifact is accepted as close evidence unchanged."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = _setup_repo(Path(tmp))
            item_path = _create_item(
                repo, status="open", work_kind="bug", blocks_release="next"
            )
            rev_path = repo / ".aw" / "records" / "reviews" / "20261011-test.review.md"
            rev_path.parent.mkdir(parents=True, exist_ok=True)
            rev_path.write_text("# Review record\n", encoding="utf-8")
            rel_rev = str(rev_path.relative_to(repo)).replace("\\", "/")

            verdict = check_engine.evaluate_blocking_close(
                repo, item_path, "done", evidence=rel_rev
            )
            self.assertTrue(verdict.legitimate)
            self.assertEqual(verdict.path, "SATISFIED")

            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                rc = cli.main(
                    [
                        "backlog",
                        "set",
                        "done",
                        "bk0001",
                        "--evidence",
                        rel_rev,
                        "--yes",
                        "--no-commit",
                        "--dir",
                        str(repo),
                    ]
                )
            self.assertEqual(rc, 0)
            found = _find_item(repo, "bk0001")
            self.assertEqual(found.parent.name, "done")

    def test_case_f_release_artifact_accepted(self) -> None:
        """A release records artifact is accepted as close evidence unchanged."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = _setup_repo(Path(tmp))
            item_path = _create_item(
                repo, status="open", work_kind="bug", blocks_release="next"
            )
            rel_release = ".aw/records/releases/20260901-rel001-01-rel001-v1.release.md"

            verdict = check_engine.evaluate_blocking_close(
                repo, item_path, "done", evidence=rel_release
            )
            self.assertTrue(verdict.legitimate)
            self.assertEqual(verdict.path, "SATISFIED")

            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                rc = cli.main(
                    [
                        "backlog",
                        "set",
                        "done",
                        "bk0001",
                        "--evidence",
                        rel_release,
                        "--yes",
                        "--no-commit",
                        "--dir",
                        str(repo),
                    ]
                )
            self.assertEqual(rc, 0)
            found = _find_item(repo, "bk0001")
            self.assertEqual(found.parent.name, "done")

    # =========================================================================
    # Case (g): at-rest consistency checker flags pending plan, passes executed plan
    # =========================================================================

    def test_case_g_pending_plan_at_rest_flagged(self) -> None:
        """At-rest release gate consistency flags a done item citing a pending plan."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = _setup_repo(Path(tmp))
            subprocess.run(["git", "init", str(repo)], check=True, capture_output=True)
            subprocess.run(
                ["git", "-C", str(repo), "config", "user.name", "Tester"], check=True
            )
            subprocess.run(
                ["git", "-C", str(repo), "config", "user.email", "test@example.com"],
                check=True,
            )
            (repo / ".aw" / "config").mkdir(parents=True, exist_ok=True)
            (repo / ".aw" / "config" / "project.json").write_text(
                '{"cutovers": {"release_gate_at_rest": "2026-10-01"}}\n',
                encoding="utf-8",
            )
            plan_path = _create_plan(
                repo, bucket="pending", plan_id="plnpnd", status="to-review"
            )
            rel_plan = str(plan_path.relative_to(repo)).replace("\\", "/")
            _create_item(
                repo,
                item_id="bk0001",
                status="done",
                work_kind="bug",
                blocks_release="next",
                close_evidence=rel_plan,
                history_date="2026-10-05",
            )

            subprocess.run(
                ["git", "-C", str(repo), "add", "."], check=True, capture_output=True
            )
            subprocess.run(
                ["git", "-C", str(repo), "commit", "-m", "initial with done item"],
                check=True,
                capture_output=True,
            )

            findings = check_engine.check_release_gate_consistency(repo, at_rest=True)
            rules = [f.rule for f in findings]
            self.assertIn("check.blocking-item-closed-without-gate", rules)

    def test_case_g_executed_plan_at_rest_clean(self) -> None:
        """At-rest release gate consistency returns clean for a done item citing an executed plan."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = _setup_repo(Path(tmp))
            subprocess.run(["git", "init", str(repo)], check=True, capture_output=True)
            subprocess.run(
                ["git", "-C", str(repo), "config", "user.name", "Tester"], check=True
            )
            subprocess.run(
                ["git", "-C", str(repo), "config", "user.email", "test@example.com"],
                check=True,
            )
            (repo / ".aw" / "config").mkdir(parents=True, exist_ok=True)
            (repo / ".aw" / "config" / "project.json").write_text(
                '{"cutovers": {"release_gate_at_rest": "2026-10-01"}}\n',
                encoding="utf-8",
            )
            plan_path = _create_plan(
                repo, bucket="executed", plan_id="plnexc", status="executed"
            )
            rel_plan = str(plan_path.relative_to(repo)).replace("\\", "/")
            _create_item(
                repo,
                item_id="bk0001",
                status="done",
                work_kind="bug",
                blocks_release="next",
                close_evidence=rel_plan,
                history_date="2026-10-05",
            )

            subprocess.run(
                ["git", "-C", str(repo), "add", "."], check=True, capture_output=True
            )
            subprocess.run(
                ["git", "-C", str(repo), "commit", "-m", "initial with done item"],
                check=True,
                capture_output=True,
            )

            findings = check_engine.check_release_gate_consistency(repo, at_rest=True)
            self.assertEqual(findings, [])

    # =========================================================================
    # Case (h): refusal reason names cited path and 'has not shipped', item byte-identical
    # =========================================================================

    def test_case_h_refusal_reason_names_path_and_unshipped_preserves_bytes(
        self,
    ) -> None:
        """Refusal reason names the cited path and 'has not shipped', item byte-identical."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = _setup_repo(Path(tmp))
            item_path = _create_item(
                repo, status="open", work_kind="bug", blocks_release="next"
            )
            original_bytes = item_path.read_bytes()
            plan_path = _create_plan(
                repo, bucket="pending", plan_id="plnpnd", status="to-review"
            )
            rel_plan = str(plan_path.relative_to(repo)).replace("\\", "/")

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
                        rel_plan,
                        "--yes",
                        "--no-commit",
                        "--dir",
                        str(repo),
                    ]
                )
            self.assertEqual(rc, 1)
            found = _find_item(repo, "bk0001")
            self.assertEqual(found.read_bytes(), original_bytes)

            stderr_val = err.getvalue()
            self.assertIn(rel_plan, stderr_val)
            self.assertIn("has not shipped", stderr_val)

            verdict = check_engine.evaluate_blocking_close(
                repo, item_path, "done", evidence=rel_plan
            )
            self.assertFalse(verdict.legitimate)
            self.assertIn(rel_plan, verdict.reason)
            self.assertIn("has not shipped", verdict.reason)
