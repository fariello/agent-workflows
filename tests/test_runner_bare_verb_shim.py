"""Behavioral regression coverage for runner implicit-start shim bare verbs.

Verifies that bare 'stop' and 'audit' first tokens are routed to their respective
command handlers and are not rewritten into 'start' in oc_runipd.main and
agy_runipd.main (backlog 2ohbkj, plan aka0li).
"""

from __future__ import annotations

import io
import os
import subprocess
import tempfile
import unittest
import unittest.mock
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

try:
    import fcntl
except ImportError:  # pragma: no cover
    fcntl = None

from agent_workflows import agy_runipd, oc_runipd, runner_stop
from tests.support import init_repo
from tests.test_oc_runipd import _CONFORMING_PLAN


def _init_repo_with_pending_plan(repo: Path, setid: str, id6: str) -> Path:
    init_repo(repo)
    (repo / ".gitignore").write_text(
        ".aw/state/\n.aw/worktrees/\n.aw/records/runs/\n", encoding="utf-8"
    )
    pending = repo / ".aw" / "records" / "plans" / "pending"
    pending.mkdir(parents=True)
    plan_path = pending / f"20260828-{setid}-01-{id6}-demo.ipd.md"
    plan_text = _CONFORMING_PLAN.format(id6=id6).replace(
        "- Set: demo", f"- Set: {setid}"
    )
    plan_path.write_text(plan_text, encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-qm", "initial"], cwd=repo, check=True, capture_output=True
    )
    return plan_path


class BareStopNotRewrittenTests(unittest.TestCase):
    def test_bare_stop_unknown_run_routes_to_stop_and_mints_no_run_dir(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo = Path(tmp_dir)
            _init_repo_with_pending_plan(repo, setid="stop", id6="stop01")

            with (
                unittest.mock.patch(
                    "agent_workflows.oc_runipd.run_queue",
                    side_effect=AssertionError(
                        "stop was rewritten into start and dispatched run_queue"
                    ),
                ),
                redirect_stdout(io.StringIO()) as oc_out,
                redirect_stderr(io.StringIO()) as oc_err,
            ):
                rc = oc_runipd.main(
                    [
                        "stop",
                        "run-nonexistent-abcdef",
                        "--now",
                        "--repo",
                        os.fspath(repo),
                    ]
                )
            self.assertEqual(rc, 2)
            self.assertEqual(oc_out.getvalue(), "")
            self.assertIn(
                "Run not found: run-nonexistent-abcdef (nothing was created or modified)",
                oc_err.getvalue(),
            )
            runs_dir = repo / ".aw" / "records" / "runs"
            self.assertTrue(not runs_dir.exists() or not any(runs_dir.iterdir()))

            with (
                unittest.mock.patch(
                    "agent_workflows.agy_runipd.run_queue",
                    side_effect=AssertionError(
                        "stop was rewritten into start and dispatched run_queue"
                    ),
                ),
                redirect_stdout(io.StringIO()) as agy_out,
                redirect_stderr(io.StringIO()) as agy_err,
            ):
                rc = agy_runipd.main(
                    [
                        "stop",
                        "run-nonexistent-abcdef",
                        "--now",
                        "--repo",
                        os.fspath(repo),
                    ]
                )
            self.assertEqual(rc, 2)
            self.assertEqual(agy_out.getvalue(), "")
            self.assertIn(
                "Run not found: run-nonexistent-abcdef (nothing was created or modified)",
                agy_err.getvalue(),
            )
            runs_dir = repo / ".aw" / "records" / "runs"
            self.assertTrue(not runs_dir.exists() or not any(runs_dir.iterdir()))

    @unittest.skipIf(fcntl is None, "POSIX flock required for live run lock")
    def test_bare_stop_live_run_records_request_without_minting_second_run_dir(self):
        # oc_runipd
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo = Path(tmp_dir)
            init_repo(repo)
            run_id = "run-20261016T000000Z-1111111"
            run_dir = repo / ".aw" / "records" / "runs" / run_id
            run_dir.mkdir(parents=True)
            lock_path = run_dir / "driver.lock"
            lock_fd = os.open(str(lock_path), os.O_CREAT | os.O_RDWR)
            try:
                fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                with (
                    redirect_stdout(io.StringIO()) as oc_out,
                    redirect_stderr(io.StringIO()) as oc_err,
                ):
                    rc = oc_runipd.main(
                        ["stop", run_id, "--now", "--repo", os.fspath(repo)]
                    )
                self.assertEqual(rc, 0)
                req = runner_stop.read_stop_request(run_dir)
                self.assertIsNotNone(req)
                self.assertEqual(req.level, runner_stop.LEVEL_NOW)
                self.assertIn("stop accepted: level 3 (now)", oc_out.getvalue())
                self.assertIn("aw oc run stop", oc_out.getvalue())
                self.assertEqual(oc_err.getvalue(), "")
                runs_entries = [
                    p.name for p in (repo / ".aw" / "records" / "runs").iterdir()
                ]
                self.assertEqual(runs_entries, [run_id])
            finally:
                os.close(lock_fd)

        # agy_runipd
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo = Path(tmp_dir)
            init_repo(repo)
            run_id = "run-20261016T000000Z-2222222"
            run_dir = repo / ".aw" / "records" / "runs" / run_id
            run_dir.mkdir(parents=True)
            lock_path = run_dir / "driver.lock"
            lock_fd = os.open(str(lock_path), os.O_CREAT | os.O_RDWR)
            try:
                fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                with (
                    redirect_stdout(io.StringIO()) as agy_out,
                    redirect_stderr(io.StringIO()) as agy_err,
                ):
                    rc = agy_runipd.main(
                        ["stop", run_id, "--now", "--repo", os.fspath(repo)]
                    )
                self.assertEqual(rc, 0)
                req = runner_stop.read_stop_request(run_dir)
                self.assertIsNotNone(req)
                self.assertEqual(req.level, runner_stop.LEVEL_NOW)
                self.assertIn("stop accepted: level 3 (now)", agy_out.getvalue())
                self.assertIn("aw agy run stop", agy_out.getvalue())
                self.assertEqual(agy_err.getvalue(), "")
                runs_entries = [
                    p.name for p in (repo / ".aw" / "records" / "runs").iterdir()
                ]
                self.assertEqual(runs_entries, [run_id])
            finally:
                os.close(lock_fd)


class BareAuditNotRewrittenTests(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp_dir.name)
        _init_repo_with_pending_plan(self.repo, setid="audit", id6="audt01")

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_bare_audit_with_matching_pending_set_routes_to_audit_and_mints_no_run_dir(
        self,
    ):
        with (
            unittest.mock.patch(
                "agent_workflows.oc_runipd.run_queue",
                side_effect=AssertionError(
                    "audit was rewritten into start and dispatched run_queue"
                ),
            ),
            redirect_stdout(io.StringIO()) as oc_out,
            redirect_stderr(io.StringIO()) as oc_err,
        ):
            rc = oc_runipd.main(["audit", "audt01", "--repo", os.fspath(self.repo)])
        self.assertEqual(rc, 1)
        self.assertEqual(oc_out.getvalue(), "")
        self.assertIn("audit refused (audit-plan-not-executed)", oc_err.getvalue())
        runs_dir = self.repo / ".aw" / "records" / "runs"
        self.assertTrue(not runs_dir.exists() or not any(runs_dir.iterdir()))

        with (
            unittest.mock.patch(
                "agent_workflows.agy_runipd.run_queue",
                side_effect=AssertionError(
                    "audit was rewritten into start and dispatched run_queue"
                ),
            ),
            redirect_stdout(io.StringIO()) as agy_out,
            redirect_stderr(io.StringIO()) as agy_err,
        ):
            rc = agy_runipd.main(["audit", "audt01", "--repo", os.fspath(self.repo)])
        self.assertEqual(rc, 2)
        self.assertEqual(agy_out.getvalue(), "")
        self.assertIn(
            "audit is not implemented on the Antigravity host", agy_err.getvalue()
        )
        self.assertIn("aw oc run audit audt01", agy_err.getvalue())
        runs_dir = self.repo / ".aw" / "records" / "runs"
        self.assertTrue(not runs_dir.exists() or not any(runs_dir.iterdir()))

    def test_bare_audit_unknown_plan_routes_to_audit_and_mints_no_run_dir(self):
        with (
            redirect_stdout(io.StringIO()) as oc_out,
            redirect_stderr(io.StringIO()) as oc_err,
        ):
            rc = oc_runipd.main(["audit", "nosuch", "--repo", os.fspath(self.repo)])
        self.assertEqual(rc, 1)
        self.assertEqual(oc_out.getvalue(), "")
        self.assertIn("audit refused (audit-plan-not-found)", oc_err.getvalue())
        runs_dir = self.repo / ".aw" / "records" / "runs"
        self.assertTrue(not runs_dir.exists() or not any(runs_dir.iterdir()))

        with (
            redirect_stdout(io.StringIO()) as agy_out,
            redirect_stderr(io.StringIO()) as agy_err,
        ):
            rc = agy_runipd.main(["audit", "nosuch", "--repo", os.fspath(self.repo)])
        self.assertEqual(rc, 2)
        self.assertEqual(agy_out.getvalue(), "")
        self.assertIn(
            "audit is not implemented on the Antigravity host", agy_err.getvalue()
        )
        self.assertIn("aw oc run audit nosuch", agy_err.getvalue())
        runs_dir = self.repo / ".aw" / "records" / "runs"
        self.assertTrue(not runs_dir.exists() or not any(runs_dir.iterdir()))
