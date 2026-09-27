"""Tests for closescope 2a6phj: require an executed carrier before a release-blocking backlog item closes done on the handoff route.

Validates the close-legitimacy behavior for release-gated backlog items:
(1) PENDING same-gate plan only -> done REFUSED (rc 1), item in graduated/, stderr names graduated.
(2) EXECUTED plan -> done allowed (rc 0, item in done/).
(3) PENDING plan, target graduated from open -> allowed (rc 0).
(4) SPEC carrier: approved spec refused, implemented spec allowed.
(5) TWO carriers, one pending and one executed -> allowed.
(6) SATISFIED unchanged: pending plan only, --evidence -> allowed, verdict.path is SATISFIED.
(7) DE-GATED unchanged: pending plan only, --blocks-release - -> allowed.
(8) SUPERSEDED or NOT-EXECUTED plan as only carrier -> refused.
(9) Spec mismatch: field trusts implemented over approved regardless of directory.
"""

from __future__ import annotations

import contextlib
import io
import os
import subprocess
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Optional

from agent_workflows import check_engine
from agent_workflows import cli


def _make_scratch_repo(root: Path) -> Path:
    """Create a minimal scratch git repository with required record directories."""
    repo = root / "repo"
    repo.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-b", "main", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test Runner"], cwd=repo, check=True)
    subprocess.run(
        ["git", "config", "user.email", "tester@example.com"], cwd=repo, check=True
    )

    for p in (
        repo / ".aw" / "records" / "releases",
        repo / ".aw" / "records" / "backlog" / "open",
        repo / ".aw" / "records" / "backlog" / "graduated",
        repo / ".aw" / "records" / "backlog" / "done",
        repo / ".aw" / "records" / "plans" / "pending",
        repo / ".aw" / "records" / "plans" / "executed",
        repo / ".aw" / "records" / "plans" / "superseded",
        repo / ".aw" / "records" / "plans" / "not-executed",
        repo / ".aw" / "records" / "specs" / "approved",
        repo / ".aw" / "records" / "specs" / "implemented",
    ):
        p.mkdir(parents=True, exist_ok=True)

    rel_file = (
        repo
        / ".aw"
        / "records"
        / "releases"
        / "20260901-rel001-01-rel001-v1.release.md"
    )
    rel_file.write_text(
        "# Release: 1.0.0\n\n"
        "- Id: rel001\n"
        "- Status: planned\n"
        "- Version: 1.0.0\n"
        "- Summary: Test release\n",
        encoding="utf-8",
    )
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "init", "-q"], cwd=repo, check=True)
    return repo


def _write_backlog_item(
    repo: Path,
    item_id: str,
    status: str = "graduated",
    blocks_release: Optional[str] = "next",
) -> Path:
    br_line = f"- Blocks-Release: {blocks_release}\n" if blocks_release else ""
    item_path = (
        repo
        / ".aw"
        / "records"
        / "backlog"
        / status
        / f"20260920-{item_id}-01-{item_id}-test-item.backlog.md"
    )
    item_path.write_text(
        f"- Id: {item_id}\n"
        f"- Status: {status}\n"
        f"{br_line}"
        f"- Set: testset\n"
        f"- Priority: high\n"
        f"- Work-Kind: bug\n"
        f"- Summary: Test item {item_id}\n\n"
        f"## Summary\nTest item.\n",
        encoding="utf-8",
    )
    subprocess.run(["git", "add", str(item_path)], cwd=repo, check=True)
    subprocess.run(
        ["git", "commit", "-m", f"add backlog {item_id}", "-q"],
        cwd=repo,
        check=True,
    )
    return item_path


def _write_plan(
    repo: Path,
    plan_id: str,
    bucket: str = "pending",
    status: str = "approved",
    from_backlog: Optional[str] = "item01",
    blocks_release: Optional[str] = "next",
) -> Path:
    fb_line = f"- From-Backlog: {from_backlog}\n" if from_backlog else ""
    br_line = f"- Blocks-Release: {blocks_release}\n" if blocks_release else ""
    plan_path = (
        repo
        / ".aw"
        / "records"
        / "plans"
        / bucket
        / f"20260926-testset-01-{plan_id}-test-plan.ipd.md"
    )
    plan_path.write_text(
        f"# IPD: Test plan {plan_id}\n\n"
        f"- Id: {plan_id}\n"
        f"- Status: {status}\n"
        f"{fb_line}"
        f"{br_line}"
        f"- Set: testset\n"
        f"- Scope: Test\n"
        f"- Scope-Paths: foo.py\n\n"
        f"## Goal\nTest\n",
        encoding="utf-8",
    )
    subprocess.run(["git", "add", str(plan_path)], cwd=repo, check=True)
    subprocess.run(
        ["git", "commit", "-m", f"add plan {plan_id}", "-q"],
        cwd=repo,
        check=True,
    )
    return plan_path


def _write_spec(
    repo: Path,
    spec_id: str,
    subdir: str = "approved",
    status: str = "approved",
    from_backlog: Optional[str] = "item01",
    blocks_release: Optional[str] = "next",
) -> Path:
    fb_line = f"- From-Backlog: {from_backlog}\n" if from_backlog else ""
    br_line = f"- Blocks-Release: {blocks_release}\n" if blocks_release else ""
    spec_path = (
        repo
        / ".aw"
        / "records"
        / "specs"
        / subdir
        / f"20260926-{spec_id}-01-{spec_id}-test-spec.spec.md"
    )
    spec_path.write_text(
        f"# Spec: Test spec {spec_id}\n\n"
        f"- Id: {spec_id}\n"
        f"- Status: {status}\n"
        f"{fb_line}"
        f"{br_line}\n"
        f"## Goal\nTest\n",
        encoding="utf-8",
    )
    subprocess.run(["git", "add", str(spec_path)], cwd=repo, check=True)
    subprocess.run(
        ["git", "commit", "-m", f"add spec {spec_id}", "-q"],
        cwd=repo,
        check=True,
    )
    return spec_path


class BacklogHandoffCloseBehaviorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        tmp = Path(self.temp_dir.name)
        self.aw_home = tmp / "aw_home"
        self.xdg_home = tmp / "xdg_config"
        self.aw_home.mkdir(parents=True, exist_ok=True)
        self.xdg_home.mkdir(parents=True, exist_ok=True)

        self._prev_aw_home = os.environ.get("AW_HOME")
        self._prev_xdg = os.environ.get("XDG_CONFIG_HOME")
        os.environ["AW_HOME"] = str(self.aw_home)
        os.environ["XDG_CONFIG_HOME"] = str(self.xdg_home)

        self.repo = _make_scratch_repo(tmp)

    def tearDown(self) -> None:
        if self._prev_aw_home is not None:
            os.environ["AW_HOME"] = self._prev_aw_home
        else:
            os.environ.pop("AW_HOME", None)
        if self._prev_xdg is not None:
            os.environ["XDG_CONFIG_HOME"] = self._prev_xdg
        else:
            os.environ.pop("XDG_CONFIG_HOME", None)

    def test_case_1_pending_same_gate_plan_refused(self) -> None:
        """(1) PENDING same-gate plan only -> done REFUSED (rc 1), item STILL in graduated/, stderr names graduated."""
        item_path = _write_backlog_item(
            self.repo, "item01", status="graduated", blocks_release="next"
        )
        _write_plan(
            self.repo,
            "plan01",
            bucket="pending",
            status="approved",
            from_backlog="item01",
            blocks_release="next",
        )

        stderr_buf = io.StringIO()
        with contextlib.redirect_stderr(stderr_buf), contextlib.redirect_stdout(
            io.StringIO()
        ):
            rc = cli.main(
                [
                    "backlog",
                    "set",
                    "item01",
                    "--status",
                    "done",
                    "--dir",
                    str(self.repo),
                    "--message",
                    "close",
                ]
            )

        self.assertEqual(rc, 1)
        self.assertTrue(item_path.exists())
        done_path = self.repo / ".aw" / "records" / "backlog" / "done" / item_path.name
        self.assertFalse(done_path.exists())
        stderr_text = stderr_buf.getvalue()
        self.assertIn("graduated", stderr_text)

    def test_case_2_executed_plan_allowed(self) -> None:
        """(2) Same plan in plans/executed/ (with - Status: executed) -> done allowed (rc 0, item in done/)."""
        item_path = _write_backlog_item(
            self.repo, "item01", status="graduated", blocks_release="next"
        )
        _write_plan(
            self.repo,
            "plan01",
            bucket="executed",
            status="executed",
            from_backlog="item01",
            blocks_release="next",
        )

        stderr_buf = io.StringIO()
        with contextlib.redirect_stderr(stderr_buf), contextlib.redirect_stdout(
            io.StringIO()
        ):
            rc = cli.main(
                [
                    "backlog",
                    "set",
                    "item01",
                    "--status",
                    "done",
                    "--dir",
                    str(self.repo),
                    "--message",
                    "close",
                ]
            )

        self.assertEqual(rc, 0)
        self.assertFalse(item_path.exists())
        done_path = self.repo / ".aw" / "records" / "backlog" / "done" / item_path.name
        self.assertTrue(done_path.exists())

    def test_case_3_pending_plan_target_graduated_allowed(self) -> None:
        """(3) PENDING plan, target graduated from open -> allowed (rc 0)."""
        item_path = _write_backlog_item(
            self.repo, "item01", status="open", blocks_release="next"
        )
        _write_plan(
            self.repo,
            "plan01",
            bucket="pending",
            status="approved",
            from_backlog="item01",
            blocks_release="next",
        )

        stderr_buf = io.StringIO()
        with contextlib.redirect_stderr(stderr_buf), contextlib.redirect_stdout(
            io.StringIO()
        ):
            rc = cli.main(
                [
                    "backlog",
                    "set",
                    "item01",
                    "--status",
                    "graduated",
                    "--dir",
                    str(self.repo),
                    "--message",
                    "graduate",
                ]
            )

        self.assertEqual(rc, 0)
        self.assertFalse(item_path.exists())
        grad_path = (
            self.repo / ".aw" / "records" / "backlog" / "graduated" / item_path.name
        )
        self.assertTrue(grad_path.exists())

    def test_case_4_spec_carrier_approved_refused(self) -> None:
        """(4a) SPEC carrier: a spec under specs/approved/ with - Status: approved -> refused (rc 1)."""
        item_path = _write_backlog_item(
            self.repo, "item01", status="graduated", blocks_release="next"
        )
        _write_spec(
            self.repo,
            "spec01",
            subdir="approved",
            status="approved",
            from_backlog="item01",
            blocks_release="next",
        )

        stderr_buf = io.StringIO()
        with contextlib.redirect_stderr(stderr_buf), contextlib.redirect_stdout(
            io.StringIO()
        ):
            rc = cli.main(
                [
                    "backlog",
                    "set",
                    "item01",
                    "--status",
                    "done",
                    "--dir",
                    str(self.repo),
                    "--message",
                    "close",
                ]
            )

        self.assertEqual(rc, 1)
        self.assertTrue(item_path.exists())
        done_path = self.repo / ".aw" / "records" / "backlog" / "done" / item_path.name
        self.assertFalse(done_path.exists())
        self.assertIn("graduated", stderr_buf.getvalue())

    def test_case_4_spec_carrier_implemented_allowed(self) -> None:
        """(4b) SPEC carrier: same spec under specs/implemented/ with - Status: implemented -> allowed (rc 0)."""
        item_path = _write_backlog_item(
            self.repo, "item01", status="graduated", blocks_release="next"
        )
        _write_spec(
            self.repo,
            "spec01",
            subdir="implemented",
            status="implemented",
            from_backlog="item01",
            blocks_release="next",
        )

        stderr_buf = io.StringIO()
        with contextlib.redirect_stderr(stderr_buf), contextlib.redirect_stdout(
            io.StringIO()
        ):
            rc = cli.main(
                [
                    "backlog",
                    "set",
                    "item01",
                    "--status",
                    "done",
                    "--dir",
                    str(self.repo),
                    "--message",
                    "close",
                ]
            )

        self.assertEqual(rc, 0)
        self.assertFalse(item_path.exists())
        done_path = self.repo / ".aw" / "records" / "backlog" / "done" / item_path.name
        self.assertTrue(done_path.exists())

    def test_case_5_two_carriers_pending_and_executed_allowed(self) -> None:
        """(5) TWO carriers, one pending and one executed -> allowed (rc 0)."""
        item_path = _write_backlog_item(
            self.repo, "item01", status="graduated", blocks_release="next"
        )
        _write_plan(
            self.repo,
            "plan01",
            bucket="pending",
            status="approved",
            from_backlog="item01",
            blocks_release="next",
        )
        _write_plan(
            self.repo,
            "plan02",
            bucket="executed",
            status="executed",
            from_backlog="item01",
            blocks_release="next",
        )

        stderr_buf = io.StringIO()
        with contextlib.redirect_stderr(stderr_buf), contextlib.redirect_stdout(
            io.StringIO()
        ):
            rc = cli.main(
                [
                    "backlog",
                    "set",
                    "item01",
                    "--status",
                    "done",
                    "--dir",
                    str(self.repo),
                    "--message",
                    "close",
                ]
            )

        self.assertEqual(rc, 0)
        self.assertFalse(item_path.exists())
        done_path = self.repo / ".aw" / "records" / "backlog" / "done" / item_path.name
        self.assertTrue(done_path.exists())

    def test_case_6_satisfied_evidence_allowed(self) -> None:
        """(6) SATISFIED unchanged: pending plan only, --evidence <in-tree records path> -> allowed (rc 0), verdict.path is SATISFIED."""
        item_path = _write_backlog_item(
            self.repo, "item01", status="graduated", blocks_release="next"
        )
        _write_plan(
            self.repo,
            "plan01",
            bucket="pending",
            status="approved",
            from_backlog="item01",
            blocks_release="next",
        )
        ev_file = (
            self.repo
            / ".aw"
            / "records"
            / "releases"
            / "20260901-rel001-01-rel001-v1.release.md"
        )

        verdict = check_engine.evaluate_blocking_close(
            self.repo, item_path, "done", evidence=str(ev_file)
        )
        self.assertEqual(verdict.path, "SATISFIED")

        stderr_buf = io.StringIO()
        with contextlib.redirect_stderr(stderr_buf), contextlib.redirect_stdout(
            io.StringIO()
        ):
            rc = cli.main(
                [
                    "backlog",
                    "set",
                    "item01",
                    "--status",
                    "done",
                    "--evidence",
                    str(ev_file),
                    "--dir",
                    str(self.repo),
                    "--message",
                    "close",
                ]
            )

        self.assertEqual(rc, 0)
        self.assertFalse(item_path.exists())
        done_path = self.repo / ".aw" / "records" / "backlog" / "done" / item_path.name
        self.assertTrue(done_path.exists())

    def test_case_7_degated_allowed(self) -> None:
        """(7) DE-GATED unchanged: pending plan only, --blocks-release - in the same call -> allowed (rc 0)."""
        item_path = _write_backlog_item(
            self.repo, "item01", status="graduated", blocks_release="next"
        )
        _write_plan(
            self.repo,
            "plan01",
            bucket="pending",
            status="approved",
            from_backlog="item01",
            blocks_release="next",
        )

        stderr_buf = io.StringIO()
        with contextlib.redirect_stderr(stderr_buf), contextlib.redirect_stdout(
            io.StringIO()
        ):
            rc = cli.main(
                [
                    "backlog",
                    "set",
                    "item01",
                    "--status",
                    "done",
                    "--blocks-release",
                    "-",
                    "--dir",
                    str(self.repo),
                    "--message",
                    "close",
                ]
            )

        self.assertEqual(rc, 0)
        self.assertFalse(item_path.exists())
        done_path = self.repo / ".aw" / "records" / "backlog" / "done" / item_path.name
        self.assertTrue(done_path.exists())

    def test_case_8_superseded_or_not_executed_plan_refused(self) -> None:
        """(8) SUPERSEDED or NOT-EXECUTED plan as only carrier -> refused (terminal is not executed)."""
        item_path = _write_backlog_item(
            self.repo, "item01", status="graduated", blocks_release="next"
        )
        _write_plan(
            self.repo,
            "plan01",
            bucket="superseded",
            status="superseded",
            from_backlog="item01",
            blocks_release="next",
        )

        stderr_buf = io.StringIO()
        with contextlib.redirect_stderr(stderr_buf), contextlib.redirect_stdout(
            io.StringIO()
        ):
            rc = cli.main(
                [
                    "backlog",
                    "set",
                    "item01",
                    "--status",
                    "done",
                    "--dir",
                    str(self.repo),
                    "--message",
                    "close",
                ]
            )

        self.assertEqual(rc, 1)
        self.assertTrue(item_path.exists())

    def test_case_9_spec_field_implemented_allowed(self) -> None:
        """(9a) Spec mismatch: spec in specs/approved/ with - Status: implemented -> allowed per field."""
        item_path_a = _write_backlog_item(
            self.repo, "item01", status="graduated", blocks_release="next"
        )
        _write_spec(
            self.repo,
            "spec01",
            subdir="approved",
            status="implemented",
            from_backlog="item01",
            blocks_release="next",
        )

        stderr_buf = io.StringIO()
        with contextlib.redirect_stderr(stderr_buf), contextlib.redirect_stdout(
            io.StringIO()
        ):
            rc_a = cli.main(
                [
                    "backlog",
                    "set",
                    "item01",
                    "--status",
                    "done",
                    "--dir",
                    str(self.repo),
                    "--message",
                    "close",
                ]
            )
        self.assertEqual(rc_a, 0)
        done_path = (
            self.repo / ".aw" / "records" / "backlog" / "done" / item_path_a.name
        )
        self.assertTrue(done_path.exists())

    def test_case_9_spec_field_approved_refused(self) -> None:
        """(9b) Spec mismatch: spec in specs/implemented/ with - Status: approved -> refused per field."""
        item_path_b = _write_backlog_item(
            self.repo, "item02", status="graduated", blocks_release="next"
        )
        _write_spec(
            self.repo,
            "spec02",
            subdir="implemented",
            status="approved",
            from_backlog="item02",
            blocks_release="next",
        )

        stderr_buf_b = io.StringIO()
        with contextlib.redirect_stderr(stderr_buf_b), contextlib.redirect_stdout(
            io.StringIO()
        ):
            rc_b = cli.main(
                [
                    "backlog",
                    "set",
                    "item02",
                    "--status",
                    "done",
                    "--dir",
                    str(self.repo),
                    "--message",
                    "close",
                ]
            )
        self.assertEqual(rc_b, 1)
        self.assertTrue(item_path_b.exists())
