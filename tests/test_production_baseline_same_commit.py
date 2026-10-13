"""Tests for taking graduation/spec-production baseline from the lane's base commit.

Covers gradfix s95x79 (Order 02, Set gradfix):
- Pins that concurrent merges into main do not appear as newly produced plans (F-01..F-04).
- Case (a): backlog production with isolation on and concurrent merge into main.
- Case (b): spec production with isolation on and concurrent merge into main.
- Case (c): non-isolated backlog production with pre-existing uncommitted unrelated plan (F-08).
- Case (d): negative control: agent writing mislinked plan still refuses with unchanged message.
"""

from __future__ import annotations

import contextlib
import io
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from agent_workflows import (
    agy_runipd,
    oc_runipd,
    runner_shared,
)
from tests.test_backlog_production import (
    _make_test_repo,
    _patch_host_agent,
    _write_backlog_item,
    _write_conforming_plan as _write_conforming_backlog_plan,
)
from tests.test_spec_production import (
    _write_conforming_plan as _write_conforming_spec_plan,
    _write_spec,
)

_HOSTS = (("oc", oc_runipd), ("agy", agy_runipd))


class TestProductionBaselineSameCommit(unittest.TestCase):
    """Pin baseline calculation against concurrent merges into main and uncommitted plans."""

    def test_case_a_backlog_production_concurrent_merge(self):
        """Case (a): backlog production, isolation on: concurrent merge into main does not
        cause false BACKLOG-GRADUATE-COUNT refusal, item executes and reaches graduated.
        """
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    _write_backlog_item(repo, id6="bkl101", status="open")
                    _write_backlog_item(repo, id6="bkl999", status="open")
                    subprocess.run(["git", "add", "."], cwd=repo, check=True)
                    subprocess.run(
                        ["git", "commit", "-qm", "add backlog"], cwd=repo, check=True
                    )

                    run_id = f"run-{host_label}-bkl-conc"
                    cmd = [
                        "start",
                        "bkl101",
                        "--action",
                        "plan",
                        "--repo",
                        str(repo),
                        "--run-id",
                        run_id,
                    ]
                    args = mod.build_parser().parse_args(cmd)
                    buf = io.StringIO()
                    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(
                        buf
                    ):
                        run_dir = mod.initialize_run(args)

                    real_alloc = runner_shared.allocate_isolation_worktree

                    def wrapped_alloc(r, i):
                        # Concurrently commit an unrelated plan on main
                        _write_conforming_backlog_plan(
                            repo, id6="for001", backlog_id6="bkl999", setid="foreign"
                        )
                        subprocess.run(["git", "add", "."], cwd=repo, check=True)
                        subprocess.run(
                            [
                                "git",
                                "commit",
                                "-qm",
                                "concurrent merge of unrelated plan",
                            ],
                            cwd=repo,
                            check=True,
                        )
                        return real_alloc(r, i)

                    def fake_agent(
                        state, rdir, item, plan_path, prompt_path, attempt_no, **kwargs
                    ):
                        work_dir = kwargs.get("work_dir")
                        target = Path(work_dir) if work_dir else Path(state["repo"])
                        _write_conforming_backlog_plan(
                            target, id6="pln101", backlog_id6="bkl101", setid="demo"
                        )
                        return 0, "session", rdir / "log.txt", ["cmd"]

                    with _patch_host_agent(mod, fake_agent), mock.patch.object(
                        runner_shared,
                        "allocate_isolation_worktree",
                        side_effect=wrapped_alloc,
                    ), mock.patch.object(
                        mod,
                        "allocate_isolation_worktree",
                        side_effect=wrapped_alloc,
                    ):
                        with contextlib.redirect_stdout(
                            buf
                        ), contextlib.redirect_stderr(buf):
                            mod.run_queue(run_dir, retry_incomplete=False)

                    state = json.loads(
                        (run_dir / "state.json").read_text(encoding="utf-8")
                    )
                    item = state["queue"][0]

                    # Assert item did not fail gate and executed cleanly
                    self.assertEqual(item["status"], "executed")
                    self.assertIsNone(item.get("refusal"))

                    # Assert backlog item moved to graduated
                    bkl_files = list(
                        repo.glob(".aw/records/backlog/**/20260927-bkl101*.backlog.md")
                    )
                    self.assertEqual(len(bkl_files), 1)
                    bkl_p = bkl_files[0]
                    self.assertIn("/graduated/", str(bkl_p).replace("\\", "/"))
                    bkl_txt = bkl_p.read_text(encoding="utf-8")
                    self.assertIn("- Status: graduated", bkl_txt)

                    # Assert no BACKLOG-GRADUATE-COUNT in events
                    events_file = run_dir / "events.jsonl"
                    events = [
                        json.loads(line)
                        for line in events_file.read_text(encoding="utf-8").splitlines()
                        if line.strip()
                    ]
                    for ev in events:
                        self.assertNotIn(
                            "BACKLOG-GRADUATE-COUNT", str(ev.get("detail", ""))
                        )
                        self.assertNotIn(
                            "BACKLOG-GRADUATE-COUNT", str(ev.get("reason", ""))
                        )

                    # Foreign plan id is not among committed production paths
                    attempts = item.get("attempts", [])
                    self.assertTrue(len(attempts) > 0)
                    committed_paths = attempts[0].get(
                        "backlog_production_committed_paths", []
                    )
                    self.assertFalse(
                        any("for001" in str(p) for p in committed_paths),
                        f"foreign plan for001 should not be in committed paths: {committed_paths}",
                    )

    def test_case_b_spec_production_concurrent_merge(self):
        """Case (b): spec production, isolation on: concurrent merge into main does not
        cause false SPEC-PLAN-COUNT refusal, item executes and spec reaches implementing.
        """
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    _write_spec(repo, id6="spc101", status="approved")
                    _write_spec(repo, id6="spc999", status="approved")
                    subprocess.run(["git", "add", "."], cwd=repo, check=True)
                    subprocess.run(
                        ["git", "commit", "-qm", "add spec"], cwd=repo, check=True
                    )

                    run_id = f"run-{host_label}-spc-conc"
                    cmd = [
                        "start",
                        "spc101",
                        "--action",
                        "plan",
                        "--repo",
                        str(repo),
                        "--run-id",
                        run_id,
                    ]
                    args = mod.build_parser().parse_args(cmd)
                    buf = io.StringIO()
                    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(
                        buf
                    ):
                        run_dir = mod.initialize_run(args)

                    real_alloc = runner_shared.allocate_isolation_worktree

                    def wrapped_alloc(r, i):
                        # Concurrently commit an unrelated plan on main
                        _write_conforming_spec_plan(
                            repo, id6="for002", spec_id6="spc999", setid="foreign"
                        )
                        subprocess.run(["git", "add", "."], cwd=repo, check=True)
                        subprocess.run(
                            [
                                "git",
                                "commit",
                                "-qm",
                                "concurrent merge of unrelated plan",
                            ],
                            cwd=repo,
                            check=True,
                        )
                        return real_alloc(r, i)

                    def fake_agent(
                        state, rdir, item, plan_path, prompt_path, attempt_no, **kwargs
                    ):
                        work_dir = kwargs.get("work_dir")
                        target = Path(work_dir) if work_dir else Path(state["repo"])
                        _write_conforming_spec_plan(
                            target, id6="pln101", spec_id6="spc101", setid="demo"
                        )
                        return 0, "session", rdir / "log.txt", ["cmd"]

                    with _patch_host_agent(mod, fake_agent), mock.patch.object(
                        runner_shared,
                        "allocate_isolation_worktree",
                        side_effect=wrapped_alloc,
                    ), mock.patch.object(
                        mod,
                        "allocate_isolation_worktree",
                        side_effect=wrapped_alloc,
                    ):
                        with contextlib.redirect_stdout(
                            buf
                        ), contextlib.redirect_stderr(buf):
                            mod.run_queue(run_dir, retry_incomplete=False)

                    state = json.loads(
                        (run_dir / "state.json").read_text(encoding="utf-8")
                    )
                    item = state["queue"][0]

                    # Assert item did not fail gate and executed cleanly
                    self.assertEqual(item["status"], "executed")
                    self.assertIsNone(item.get("refusal"))

                    # Assert spec moved to implementing
                    spec_files = list(
                        repo.glob(".aw/records/specs/**/20260927-spc101*.spec.md")
                    )
                    self.assertEqual(len(spec_files), 1)
                    spec_p = spec_files[0]
                    self.assertIn("/implementing/", str(spec_p).replace("\\", "/"))
                    spec_txt = spec_p.read_text(encoding="utf-8")
                    self.assertIn("- Status: implementing", spec_txt)

                    # Assert no SPEC-PLAN-COUNT in events
                    events_file = run_dir / "events.jsonl"
                    events = [
                        json.loads(line)
                        for line in events_file.read_text(encoding="utf-8").splitlines()
                        if line.strip()
                    ]
                    for ev in events:
                        self.assertNotIn("SPEC-PLAN-COUNT", str(ev.get("detail", "")))
                        self.assertNotIn("SPEC-PLAN-COUNT", str(ev.get("reason", "")))

                    # Foreign plan id is not among committed production paths
                    attempts = item.get("attempts", [])
                    self.assertTrue(len(attempts) > 0)
                    committed_paths = attempts[0].get(
                        "spec_production_committed_paths", []
                    )
                    self.assertFalse(
                        any("for002" in str(p) for p in committed_paths),
                        f"foreign plan for002 should not be in committed paths: {committed_paths}",
                    )

    def test_case_c_non_isolated_preexisting_uncommitted_plan(self):
        """Case (c): non-isolated (--no-isolate-worktree) backlog production with a pre-existing
        uncommitted unrelated plan in shared checkout: not reported as produced (F-08).
        """
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    _write_backlog_item(repo, id6="bkl101", status="open")
                    subprocess.run(["git", "add", "."], cwd=repo, check=True)
                    subprocess.run(
                        ["git", "commit", "-qm", "add backlog"], cwd=repo, check=True
                    )

                    # Write an uncommitted unrelated plan in the shared checkout
                    _write_conforming_backlog_plan(
                        repo,
                        id6="uncomm01",
                        backlog_id6="bkl999",
                        setid="foreign",
                    )
                    # Verify it is uncommitted
                    status_out = subprocess.check_output(
                        ["git", "status", "--porcelain", "-uall"], cwd=repo, text=True
                    )
                    self.assertIn("uncomm01", status_out)

                    run_id = f"run-{host_label}-bkl-noniso"
                    cmd = [
                        "start",
                        "bkl101",
                        "--action",
                        "plan",
                        "--repo",
                        str(repo),
                        "--run-id",
                        run_id,
                        "--no-isolate-worktree",
                    ]
                    args = mod.build_parser().parse_args(cmd)
                    buf = io.StringIO()
                    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(
                        buf
                    ):
                        run_dir = mod.initialize_run(args)

                    def fake_agent(
                        state, rdir, item, plan_path, prompt_path, attempt_no, **kwargs
                    ):
                        work_dir = kwargs.get("work_dir")
                        target = Path(work_dir) if work_dir else Path(state["repo"])
                        _write_conforming_backlog_plan(
                            target, id6="pln101", backlog_id6="bkl101", setid="demo"
                        )
                        return 0, "session", rdir / "log.txt", ["cmd"]

                    with _patch_host_agent(mod, fake_agent):
                        with contextlib.redirect_stdout(
                            buf
                        ), contextlib.redirect_stderr(buf):
                            mod.run_queue(run_dir, retry_incomplete=False)

                    state = json.loads(
                        (run_dir / "state.json").read_text(encoding="utf-8")
                    )
                    item = state["queue"][0]

                    # Assert item executed cleanly
                    self.assertEqual(item["status"], "executed")
                    self.assertIsNone(item.get("refusal"))

                    # Assert backlog item moved to graduated
                    bkl_files = list(
                        repo.glob(".aw/records/backlog/**/20260927-bkl101*.backlog.md")
                    )
                    self.assertEqual(len(bkl_files), 1)
                    self.assertIn("/graduated/", str(bkl_files[0]).replace("\\", "/"))

                    # Assert uncomm01 was not committed as this item's production
                    attempts = item.get("attempts", [])
                    self.assertTrue(len(attempts) > 0)
                    committed_paths = attempts[0].get(
                        "backlog_production_committed_paths", []
                    )
                    self.assertFalse(
                        any("uncomm01" in str(p) for p in committed_paths),
                        f"uncommitted plan should not be committed: {committed_paths}",
                    )

    def test_case_d_negative_control_mislinked_plan(self):
        """Case (d): negative control: agent writing plan with wrong From-Backlog still
        refuses with unchanged BACKLOG-GRADUATE-COUNT message.
        """
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    _write_backlog_item(repo, id6="bkl101", status="open")
                    subprocess.run(["git", "add", "."], cwd=repo, check=True)
                    subprocess.run(
                        ["git", "commit", "-qm", "add backlog"], cwd=repo, check=True
                    )

                    run_id = f"run-{host_label}-bkl-neg"
                    cmd = [
                        "start",
                        "bkl101",
                        "--action",
                        "plan",
                        "--repo",
                        str(repo),
                        "--run-id",
                        run_id,
                    ]
                    args = mod.build_parser().parse_args(cmd)
                    buf = io.StringIO()
                    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(
                        buf
                    ):
                        run_dir = mod.initialize_run(args)

                    def fake_agent(
                        state, rdir, item, plan_path, prompt_path, attempt_no, **kwargs
                    ):
                        work_dir = kwargs.get("work_dir")
                        target = Path(work_dir) if work_dir else Path(state["repo"])
                        _write_conforming_backlog_plan(
                            target, id6="pbad01", backlog_id6="wrongbkl", setid="demo"
                        )
                        return 0, "session", rdir / "log.txt", ["cmd"]

                    with _patch_host_agent(mod, fake_agent):
                        with contextlib.redirect_stdout(
                            buf
                        ), contextlib.redirect_stderr(buf):
                            mod.run_queue(run_dir, retry_incomplete=False)

                    state = json.loads(
                        (run_dir / "state.json").read_text(encoding="utf-8")
                    )
                    item = state["queue"][0]

                    # Assert item failed gate
                    self.assertEqual(item["status"], "fail-gate")
                    refusal = item.get("refusal") or {}
                    self.assertEqual(refusal.get("code"), "BACKLOG-GRADUATE-COUNT")
                    self.assertIn(
                        "carrying From-Backlog",
                        refusal.get("reason", ""),
                    )

                    # Backlog item remains in open/
                    bkl_files = list(
                        repo.glob(".aw/records/backlog/**/20260927-bkl101*.backlog.md")
                    )
                    self.assertEqual(len(bkl_files), 1)
                    self.assertIn("/open/", str(bkl_files[0]).replace("\\", "/"))


if __name__ == "__main__":
    unittest.main()
