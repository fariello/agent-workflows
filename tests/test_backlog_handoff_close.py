"""Tests for closescope 2a6phj: require an executed carrier before a release-blocking backlog item closes done on the handoff route.

Validates the close-legitimacy behavior for release-gated backlog items:
(1) PENDING same-gate plan only -> done REFUSED (rc 1), item in graduated/, stderr names graduated.
(2) EXECUTED plan -> done allowed (rc 0, item in done/).
(3) PENDING plan, target graduated from open -> allowed (rc 0).
(4) SPEC carrier: approved spec refused, implemented spec allowed.
(5) TWO carriers, one pending and one executed -> refused (rc 1), both executed -> allowed (rc 0).
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
        (p / ".gitkeep").touch()

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

    def test_case_5_two_carriers_pending_and_executed_refused(self) -> None:
        """(5) TWO carriers, one pending and one executed -> refused (rc 1).

        Deliberately reversed by plan 2o5wka (backlog lsbd32, anycarrier Order 1):
        previously asserted rc 0 allowed under the permissive ANY-carrier rule authored
        by 2a6phj (OQ-03). Now requires ALL same-gate carriers to be executed.
        """
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

        self.assertEqual(rc, 1)
        self.assertTrue(item_path.exists())
        done_path = self.repo / ".aw" / "records" / "backlog" / "done" / item_path.name
        self.assertFalse(done_path.exists())
        stderr_text = stderr_buf.getvalue()
        self.assertIn("plan01", stderr_text)

    def test_case_5_two_carriers_both_executed_allowed(self) -> None:
        """(5b) TWO carriers, BOTH executed -> allowed (rc 0, path HANDOFF)."""
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
        _write_plan(
            self.repo,
            "plan02",
            bucket="executed",
            status="executed",
            from_backlog="item01",
            blocks_release="next",
        )

        verdict = check_engine.evaluate_blocking_close(self.repo, item_path, "done")
        self.assertTrue(verdict.legitimate)
        self.assertEqual(verdict.path, "HANDOFF")

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

    def test_case_5_three_carriers_two_executed_one_pending_refused(self) -> None:
        """(5c) THREE carriers, two executed and one pending -> refused (rc 1)."""
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
        _write_plan(
            self.repo,
            "plan02",
            bucket="executed",
            status="executed",
            from_backlog="item01",
            blocks_release="next",
        )
        _write_plan(
            self.repo,
            "plan03",
            bucket="pending",
            status="approved",
            from_backlog="item01",
            blocks_release="next",
        )

        verdict = check_engine.evaluate_blocking_close(self.repo, item_path, "done")
        self.assertFalse(verdict.legitimate)

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
        self.assertIn("plan03", stderr_buf.getvalue())

    def test_case_5_mixed_kind_carriers_plan_and_spec(self) -> None:
        """(5d) MIXED-KIND carriers: executed plan + approved spec -> refused (rc 1); implemented spec -> allowed (rc 0)."""
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
        spec_path = _write_spec(
            self.repo,
            "spec01",
            subdir="approved",
            status="approved",
            from_backlog="item01",
            blocks_release="next",
        )

        # Part 1: approved spec (not implemented) -> refused
        verdict = check_engine.evaluate_blocking_close(self.repo, item_path, "done")
        self.assertFalse(verdict.legitimate)

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
        self.assertIn("spec01", stderr_buf.getvalue())

        # Part 2: update spec to implemented -> allowed
        imp_dir = self.repo / ".aw" / "records" / "specs" / "implemented"
        new_spec_path = imp_dir / spec_path.name
        spec_content = spec_path.read_text(encoding="utf-8").replace(
            "- Status: approved", "- Status: implemented"
        )
        spec_path.unlink()
        new_spec_path.write_text(spec_content, encoding="utf-8")
        subprocess.run(["git", "rm", str(spec_path)], cwd=self.repo, check=True)
        subprocess.run(["git", "add", str(new_spec_path)], cwd=self.repo, check=True)
        subprocess.run(
            ["git", "commit", "-m", "implement spec01", "-q"],
            cwd=self.repo,
            check=True,
        )

        verdict2 = check_engine.evaluate_blocking_close(self.repo, item_path, "done")
        self.assertTrue(verdict2.legitimate)
        self.assertEqual(verdict2.path, "HANDOFF")

        stderr_buf2 = io.StringIO()
        with contextlib.redirect_stderr(stderr_buf2), contextlib.redirect_stdout(
            io.StringIO()
        ):
            rc2 = cli.main(
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
        self.assertEqual(rc2, 0)
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

    def test_case_6a_satisfied_evidence_at_rest_reconstructable(self) -> None:
        """(6a) Motivates set: gated done item closed with --evidence reconstructs SATISFIED at rest."""
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
        rel_ev = ev_file.relative_to(self.repo).as_posix()

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
                    rel_ev,
                    "--dir",
                    str(self.repo),
                    "--message",
                    "close on evidence",
                ]
            )

        self.assertEqual(rc, 0)
        done_path = self.repo / ".aw" / "records" / "backlog" / "done" / item_path.name
        self.assertTrue(done_path.exists())

        # Ask evaluate_blocking_close about the WRITTEN item with NO evidence= argument
        verdict = check_engine.evaluate_blocking_close(self.repo, done_path, "done")
        self.assertTrue(verdict.legitimate)
        self.assertEqual(verdict.path, "SATISFIED")

    def test_case_6b_satisfied_evidence_bullet_removed_refused(self) -> None:
        """(6b) Same item with Close-Evidence bullet removed is refused (fail-closed)."""
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
        rel_ev = ev_file.relative_to(self.repo).as_posix()

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
                    rel_ev,
                    "--dir",
                    str(self.repo),
                    "--message",
                    "close on evidence",
                ]
            )
        self.assertEqual(rc, 0)
        done_path = self.repo / ".aw" / "records" / "backlog" / "done" / item_path.name
        self.assertTrue(done_path.exists())

        # Remove the - Close-Evidence: bullet if present, or ensure it is absent
        content = done_path.read_text(encoding="utf-8")
        lines = [
            line
            for line in content.splitlines(keepends=True)
            if not line.startswith("- Close-Evidence:")
        ]
        done_path.write_text("".join(lines), encoding="utf-8")

        verdict = check_engine.evaluate_blocking_close(self.repo, done_path, "done")
        self.assertFalse(verdict.legitimate)
        self.assertEqual(verdict.severity, "error")

    def test_case_6c_satisfied_evidence_nonexistent_path_refused(self) -> None:
        """(6c) Item carrying Close-Evidence pointing to nonexistent artifact is refused."""
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
        done_path = self.repo / ".aw" / "records" / "backlog" / "done" / item_path.name
        content = (
            "- Id: item01\n"
            "- Status: done\n"
            "- Blocks-Release: next\n"
            "- Close-Evidence: .aw/records/plans/nonexistent.ipd.md\n"
            "- Set: testset\n"
            "- Priority: high\n"
            "- Work-Kind: bug\n"
            "- Summary: Test item item01\n\n"
            "## Summary\nTest item.\n"
        )
        done_path.write_text(content, encoding="utf-8")
        item_path.unlink()

        verdict = check_engine.evaluate_blocking_close(self.repo, done_path, "done")
        self.assertFalse(verdict.legitimate)
        self.assertEqual(verdict.severity, "error")

    def test_case_6d_handoff_and_degated_closes_leave_no_close_evidence(self) -> None:
        """(6d) HANDOFF close (even if --evidence passed) and DE-GATED close leave NO Close-Evidence bullet."""
        # 1. HANDOFF close with executed plan and --evidence passed
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
        ev_file = (
            self.repo
            / ".aw"
            / "records"
            / "releases"
            / "20260901-rel001-01-rel001-v1.release.md"
        )
        rel_ev = ev_file.relative_to(self.repo).as_posix()

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
                    rel_ev,
                    "--dir",
                    str(self.repo),
                    "--message",
                    "close handoff",
                ]
            )
        self.assertEqual(rc, 0)
        done_path = self.repo / ".aw" / "records" / "backlog" / "done" / item_path.name
        self.assertTrue(done_path.exists())
        self.assertNotIn("- Close-Evidence:", done_path.read_text(encoding="utf-8"))

        # 2. DE-GATED close with --blocks-release -
        item_path2 = _write_backlog_item(
            self.repo, "item02", status="graduated", blocks_release="next"
        )
        _write_plan(
            self.repo,
            "plan02",
            bucket="pending",
            status="approved",
            from_backlog="item02",
            blocks_release="next",
        )
        with contextlib.redirect_stderr(io.StringIO()), contextlib.redirect_stdout(
            io.StringIO()
        ):
            rc2 = cli.main(
                [
                    "backlog",
                    "set",
                    "item02",
                    "--status",
                    "done",
                    "--blocks-release",
                    "-",
                    "--dir",
                    str(self.repo),
                    "--message",
                    "close degated",
                ]
            )
        self.assertEqual(rc2, 0)
        done_path2 = (
            self.repo / ".aw" / "records" / "backlog" / "done" / item_path2.name
        )
        self.assertTrue(done_path2.exists())
        self.assertNotIn("- Close-Evidence:", done_path2.read_text(encoding="utf-8"))

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


class BacklogGateDirSplitTests(unittest.TestCase):
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

        self.main_repo = _make_scratch_repo(tmp / "main_repo")
        lane_path = tmp / "lane_repo"
        subprocess.run(
            ["git", "worktree", "add", "-b", "lane", str(lane_path), "main"],
            cwd=self.main_repo,
            check=True,
            capture_output=True,
        )
        self.lane_repo = lane_path

    def tearDown(self) -> None:
        if self._prev_aw_home is not None:
            os.environ["AW_HOME"] = self._prev_aw_home
        else:
            os.environ.pop("AW_HOME", None)
        if self._prev_xdg is not None:
            os.environ["XDG_CONFIG_HOME"] = self._prev_xdg
        else:
            os.environ.pop("XDG_CONFIG_HOME", None)

    def _run_cli(self, argv: list[str]) -> tuple[int, str, str]:
        stdout_buf = io.StringIO()
        stderr_buf = io.StringIO()
        with contextlib.redirect_stderr(stderr_buf), contextlib.redirect_stdout(
            stdout_buf
        ):
            try:
                rc = cli.main(argv)
            except SystemExit as exc:
                rc = exc.code if isinstance(exc.code, int) else 2
        return rc, stdout_buf.getvalue(), stderr_buf.getvalue()

    def test_case_1_two_carrier_sibling_unexecuted_gate_dir_refused(self) -> None:
        """(1) Two-carrier item with unexecuted sibling: gate against main refuses (rc 1), move in lane."""
        item_lane = _write_backlog_item(
            self.lane_repo, "item01", status="open", blocks_release="next"
        )
        _write_plan(
            self.lane_repo,
            "plan01",
            bucket="executed",
            status="executed",
            from_backlog="item01",
            blocks_release="next",
        )
        _write_plan(
            self.lane_repo,
            "plan02",
            bucket="pending",
            status="approved",
            from_backlog="item01",
            blocks_release="next",
        )

        _write_backlog_item(
            self.main_repo, "item01", status="open", blocks_release="next"
        )
        _write_plan(
            self.main_repo,
            "plan01",
            bucket="pending",
            status="approved",
            from_backlog="item01",
            blocks_release="next",
        )
        _write_plan(
            self.main_repo,
            "plan02",
            bucket="pending",
            status="approved",
            from_backlog="item01",
            blocks_release="next",
        )

        rc, stdout_text, stderr_text = self._run_cli(
            [
                "backlog",
                "set",
                "item01",
                "--status",
                "done",
                "--dir",
                str(self.lane_repo),
                "--gate-dir",
                str(self.main_repo),
                "--message",
                "close",
            ]
        )
        self.assertEqual(rc, 1)
        self.assertIn("carrier is not executed/implemented", stderr_text)
        self.assertTrue(item_lane.exists())
        done_path = (
            self.lane_repo / ".aw" / "records" / "backlog" / "done" / item_lane.name
        )
        self.assertFalse(done_path.exists())

    def test_case_2_default_is_unchanged_without_gate_dir(self) -> None:
        """(2) Same fixture as test_case_2_executed_plan_allowed: without --gate-dir, close succeeds."""
        item_path = _write_backlog_item(
            self.lane_repo, "item01", status="graduated", blocks_release="next"
        )
        _write_plan(
            self.lane_repo,
            "plan01",
            bucket="executed",
            status="executed",
            from_backlog="item01",
            blocks_release="next",
        )

        rc, stdout_text, stderr_text = self._run_cli(
            [
                "backlog",
                "set",
                "item01",
                "--status",
                "done",
                "--dir",
                str(self.lane_repo),
                "--message",
                "close",
            ]
        )
        self.assertEqual(rc, 0)
        done_path = (
            self.lane_repo / ".aw" / "records" / "backlog" / "done" / item_path.name
        )
        self.assertTrue(done_path.exists())

    def test_case_3_move_still_lands_in_move_tree(self) -> None:
        """(3) With --gate-dir pointing elsewhere, item moves in move tree and gate tree is untouched."""
        item_lane = _write_backlog_item(
            self.lane_repo, "item01", status="open", blocks_release="next"
        )
        _write_plan(
            self.lane_repo,
            "plan01",
            bucket="pending",
            status="approved",
            from_backlog="item01",
            blocks_release="next",
        )

        item_main = _write_backlog_item(
            self.main_repo, "item01", status="open", blocks_release="next"
        )
        _write_plan(
            self.main_repo,
            "plan01",
            bucket="executed",
            status="executed",
            from_backlog="item01",
            blocks_release="next",
        )

        rc, stdout_text, stderr_text = self._run_cli(
            [
                "backlog",
                "set",
                "item01",
                "--status",
                "done",
                "--dir",
                str(self.lane_repo),
                "--gate-dir",
                str(self.main_repo),
                "--message",
                "close",
            ]
        )
        self.assertEqual(rc, 0)
        # Move tree (lane): item moved from open/ to done/
        self.assertFalse(item_lane.exists())
        self.assertTrue(
            (
                self.lane_repo / ".aw" / "records" / "backlog" / "done" / item_lane.name
            ).exists()
        )
        # Gate tree (main): item untouched in open/, not in done/
        self.assertTrue(item_main.exists())
        self.assertFalse(
            (
                self.main_repo / ".aw" / "records" / "backlog" / "done" / item_main.name
            ).exists()
        )

    def test_case_4_evidence_resolved_in_gate_tree_not_move_tree(self) -> None:
        """(4) Evidence citation resolves in gate tree, not move tree."""
        item_lane = _write_backlog_item(
            self.lane_repo, "item01", status="open", blocks_release="next"
        )
        _write_plan(
            self.lane_repo,
            "plan01",
            bucket="pending",
            status="approved",
            from_backlog="item01",
            blocks_release="next",
        )
        gate_doc = (
            self.main_repo
            / ".aw"
            / "records"
            / "plans"
            / "executed"
            / "20260901-testset-01-ext001-gate-doc.ipd.md"
        )
        gate_doc.write_text(
            "# IPD: Gate doc\n\n- Id: ext001\n- Status: executed\n- Set: testset\n- Scope: T\n- Scope-Paths: x\n",
            encoding="utf-8",
        )
        subprocess.run(["git", "add", str(gate_doc)], cwd=self.main_repo, check=True)
        subprocess.run(
            ["git", "commit", "-m", "add gate doc", "-q"],
            cwd=self.main_repo,
            check=True,
        )
        rel_gate_doc = (
            ".aw/records/plans/executed/20260901-testset-01-ext001-gate-doc.ipd.md"
        )

        lane_doc = (
            self.lane_repo
            / ".aw"
            / "records"
            / "plans"
            / "executed"
            / "20260901-testset-01-ext002-lane-doc.ipd.md"
        )
        lane_doc.write_text(
            "# IPD: Lane doc\n\n- Id: ext002\n- Status: executed\n- Set: testset\n- Scope: T\n- Scope-Paths: x\n",
            encoding="utf-8",
        )
        subprocess.run(["git", "add", str(lane_doc)], cwd=self.lane_repo, check=True)
        subprocess.run(
            ["git", "commit", "-m", "add lane doc", "-q"],
            cwd=self.lane_repo,
            check=True,
        )
        rel_lane_doc = (
            ".aw/records/plans/executed/20260901-testset-01-ext002-lane-doc.ipd.md"
        )

        # (4a) Citing evidence that exists ONLY in gate tree succeeds
        rc_a, stdout_text_a, stderr_text_a = self._run_cli(
            [
                "backlog",
                "set",
                "item01",
                "--status",
                "done",
                "--dir",
                str(self.lane_repo),
                "--gate-dir",
                str(self.main_repo),
                "--evidence",
                rel_gate_doc,
                "--message",
                "close via gate evidence",
            ]
        )
        self.assertEqual(rc_a, 0)
        self.assertTrue(
            (
                self.lane_repo / ".aw" / "records" / "backlog" / "done" / item_lane.name
            ).exists()
        )

        # (4b) Citing evidence that exists ONLY in move tree fails
        item_lane_2 = _write_backlog_item(
            self.lane_repo, "item02", status="open", blocks_release="next"
        )
        _write_plan(
            self.lane_repo,
            "plan02",
            bucket="pending",
            status="approved",
            from_backlog="item02",
            blocks_release="next",
        )
        rc_b, stdout_text_b, stderr_text_b = self._run_cli(
            [
                "backlog",
                "set",
                "item02",
                "--status",
                "done",
                "--dir",
                str(self.lane_repo),
                "--gate-dir",
                str(self.main_repo),
                "--evidence",
                rel_lane_doc,
                "--message",
                "close via lane evidence",
            ]
        )
        self.assertEqual(rc_b, 1)
        self.assertIn("refused", stderr_text_b)
        self.assertTrue(item_lane_2.exists())

    def test_backlog_set_declared_flag_surface_matches_parser(self) -> None:
        """gatedir 9vglxd E-03: `--gate-dir` is DECLARED, not merely accepted, so the two cannot drift."""
        from agent_workflows.cli import _build_parser
        from agent_workflows import command_surface as cs

        decl = cs.get_declaration("backlog set")
        self.assertIsNotNone(decl)
        self.assertIn("--gate-dir", decl.legacy_flags)
        self.assertIn("--lane-carrier-ref", decl.legacy_flags)
        self.assertIn("--lane-carrier-path", decl.legacy_flags)
        backlog_parser = None
        for action in _build_parser()._actions:  # noqa: SLF001
            choices = getattr(action, "choices", None)
            if choices and hasattr(choices, "get") and choices.get("backlog"):
                backlog_parser = choices["backlog"]
                break
        self.assertIsNotNone(backlog_parser, "no `backlog` subparser")
        inner = {}
        for action in backlog_parser._actions:  # noqa: SLF001
            choices = getattr(action, "choices", None)
            if choices and hasattr(choices, "items"):
                inner.update(choices)
        accepted = {opt for act in inner["set"]._actions for opt in act.option_strings}  # noqa: SLF001
        self.assertEqual(set(decl.legacy_flags) - accepted, set())

    def test_case_5_gate_dir_non_project_root_refused(self) -> None:
        """(5) --gate-dir naming a non-project tree is refused with exit 2 and names the flag, not item."""
        non_project = Path(self.temp_dir.name) / "empty_dir"
        non_project.mkdir()
        rc, stdout_text, stderr_text = self._run_cli(
            [
                "backlog",
                "set",
                "item01",
                "--status",
                "done",
                "--dir",
                str(self.lane_repo),
                "--gate-dir",
                str(non_project),
                "--message",
                "close",
            ]
        )
        self.assertEqual(rc, 2)
        self.assertIn("--gate-dir", stderr_text)
        self.assertIn("not an agent-workflows project root", stderr_text)
        self.assertNotIn("item01", stderr_text)

    def test_case_6_single_carrier_with_lane_carrier_override_allowed(self) -> None:
        """(6) Single carrier with verified override: gate against main passes (rc 0), move in lane."""
        item_lane = _write_backlog_item(
            self.lane_repo, "item01", status="graduated", blocks_release="next"
        )
        _write_plan(
            self.main_repo,
            "plan01",
            bucket="pending",
            status="approved",
            from_backlog="item01",
            blocks_release="next",
        )
        plan_exec = (
            self.lane_repo
            / ".aw"
            / "records"
            / "plans"
            / "executed"
            / "20260926-testset-01-plan01-test-plan.ipd.md"
        )
        plan_exec.write_text(
            "# IPD: Test plan plan01\n\n- Id: plan01\n- Status: executed\n- From-Backlog: item01\n- Blocks-Release: next\n- Set: testset\n- Scope: T\n- Scope-Paths: x\n\n## Goal\nTest\n",
            encoding="utf-8",
        )
        subprocess.run(["git", "add", str(plan_exec)], cwd=self.lane_repo, check=True)
        subprocess.run(
            ["git", "commit", "-m", "execute plan01 in lane", "-q"],
            cwd=self.lane_repo,
            check=True,
        )

        rc, stdout_text, stderr_text = self._run_cli(
            [
                "backlog",
                "set",
                "item01",
                "--status",
                "done",
                "--dir",
                str(self.lane_repo),
                "--gate-dir",
                str(self.main_repo),
                "--lane-carrier-ref",
                "lane",
                "--lane-carrier-path",
                ".aw/records/plans/pending/20260926-testset-01-plan01-test-plan.ipd.md",
                "--message",
                "close single carrier with override",
            ]
        )
        self.assertEqual(rc, 0)
        self.assertFalse(item_lane.exists())
        done_path = (
            self.lane_repo / ".aw" / "records" / "backlog" / "done" / item_lane.name
        )
        self.assertTrue(done_path.exists())

    def test_case_6b_single_carrier_without_override_refused_proves_tightening(
        self,
    ) -> None:
        """(6b) Single carrier without override: gate against main refuses (rc 1, carrier not executed), proving tightening."""
        item_lane = _write_backlog_item(
            self.lane_repo, "item01", status="graduated", blocks_release="next"
        )
        _write_plan(
            self.main_repo,
            "plan01",
            bucket="pending",
            status="approved",
            from_backlog="item01",
            blocks_release="next",
        )
        plan_exec = (
            self.lane_repo
            / ".aw"
            / "records"
            / "plans"
            / "executed"
            / "20260926-testset-01-plan01-test-plan.ipd.md"
        )
        plan_exec.write_text(
            "# IPD: Test plan plan01\n\n- Id: plan01\n- Status: executed\n- From-Backlog: item01\n- Blocks-Release: next\n- Set: testset\n- Scope: T\n- Scope-Paths: x\n\n## Goal\nTest\n",
            encoding="utf-8",
        )
        subprocess.run(["git", "add", str(plan_exec)], cwd=self.lane_repo, check=True)
        subprocess.run(
            ["git", "commit", "-m", "execute plan01 in lane", "-q"],
            cwd=self.lane_repo,
            check=True,
        )

        rc, stdout_text, stderr_text = self._run_cli(
            [
                "backlog",
                "set",
                "item01",
                "--status",
                "done",
                "--dir",
                str(self.lane_repo),
                "--gate-dir",
                str(self.main_repo),
                "--message",
                "close single carrier without override",
            ]
        )
        self.assertEqual(rc, 1)
        self.assertIn("carrier is not executed/implemented", stderr_text)
        self.assertTrue(item_lane.exists())
        done_path = (
            self.lane_repo / ".aw" / "records" / "backlog" / "done" / item_lane.name
        )
        self.assertFalse(done_path.exists())

    def test_case_7_two_carrier_sibling_unexecuted_with_override_refused(self) -> None:
        """(7) Sibling unexecuted guard: override on plan01 refuses (rc 1) because plan02 sibling is pending."""
        item_lane = _write_backlog_item(
            self.lane_repo, "item01", status="graduated", blocks_release="next"
        )
        _write_plan(
            self.main_repo,
            "plan01",
            bucket="pending",
            status="approved",
            from_backlog="item01",
            blocks_release="next",
        )
        _write_plan(
            self.main_repo,
            "plan02",
            bucket="pending",
            status="approved",
            from_backlog="item01",
            blocks_release="next",
        )
        plan_exec = (
            self.lane_repo
            / ".aw"
            / "records"
            / "plans"
            / "executed"
            / "20260926-testset-01-plan01-test-plan.ipd.md"
        )
        plan_exec.write_text(
            "# IPD: Test plan plan01\n\n- Id: plan01\n- Status: executed\n- From-Backlog: item01\n- Blocks-Release: next\n- Set: testset\n- Scope: T\n- Scope-Paths: x\n\n## Goal\nTest\n",
            encoding="utf-8",
        )
        subprocess.run(["git", "add", str(plan_exec)], cwd=self.lane_repo, check=True)
        subprocess.run(
            ["git", "commit", "-m", "execute plan01 in lane", "-q"],
            cwd=self.lane_repo,
            check=True,
        )

        rc, stdout_text, stderr_text = self._run_cli(
            [
                "backlog",
                "set",
                "item01",
                "--status",
                "done",
                "--dir",
                str(self.lane_repo),
                "--gate-dir",
                str(self.main_repo),
                "--lane-carrier-ref",
                "lane",
                "--lane-carrier-path",
                ".aw/records/plans/pending/20260926-testset-01-plan01-test-plan.ipd.md",
                "--message",
                "close sibling unexecuted",
            ]
        )
        self.assertEqual(rc, 1)
        self.assertIn("carrier is not executed/implemented", stderr_text)
        self.assertTrue(item_lane.exists())
        done_path = (
            self.lane_repo / ".aw" / "records" / "backlog" / "done" / item_lane.name
        )
        self.assertFalse(done_path.exists())

    def test_case_8_forged_assertion_refused(self) -> None:
        """(8) Forged assertion: override naming ref showing pending carrier is refused (rc 1)."""
        item_lane = _write_backlog_item(
            self.lane_repo, "item01", status="graduated", blocks_release="next"
        )
        _write_plan(
            self.main_repo,
            "plan01",
            bucket="pending",
            status="approved",
            from_backlog="item01",
            blocks_release="next",
        )
        plan_exec = (
            self.lane_repo
            / ".aw"
            / "records"
            / "plans"
            / "executed"
            / "20260926-testset-01-plan01-test-plan.ipd.md"
        )
        plan_exec.write_text(
            "# IPD: Test plan plan01\n\n- Id: plan01\n- Status: executed\n- From-Backlog: item01\n- Blocks-Release: next\n- Set: testset\n- Scope: T\n- Scope-Paths: x\n\n## Goal\nTest\n",
            encoding="utf-8",
        )
        subprocess.run(["git", "add", str(plan_exec)], cwd=self.lane_repo, check=True)
        subprocess.run(
            ["git", "commit", "-m", "execute plan01 in lane", "-q"],
            cwd=self.lane_repo,
            check=True,
        )

        # Ref 'main' still has plan01 in pending/
        rc, stdout_text, stderr_text = self._run_cli(
            [
                "backlog",
                "set",
                "item01",
                "--status",
                "done",
                "--dir",
                str(self.lane_repo),
                "--gate-dir",
                str(self.main_repo),
                "--lane-carrier-ref",
                "main",
                "--lane-carrier-path",
                ".aw/records/plans/pending/20260926-testset-01-plan01-test-plan.ipd.md",
                "--message",
                "close forged assertion",
            ]
        )
        self.assertEqual(rc, 1)
        self.assertIn("carrier is not executed/implemented", stderr_text)
        self.assertTrue(item_lane.exists())
        done_path = (
            self.lane_repo / ".aw" / "records" / "backlog" / "done" / item_lane.name
        )
        self.assertFalse(done_path.exists())
