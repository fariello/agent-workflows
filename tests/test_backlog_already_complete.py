"""Tests for closing a backlog item whose carriers are already complete (IPD 0owirm, Set gradfix).

Covers:
- E-02: Unit tests for backlog_item_already_complete predicate.
- E-05: Matrix across both hosts:
  (a) every IPD carrier executed: item closed done, agent never called, backlog-already-complete event present, queue executed;
      run once with --no-isolate-worktree and once with isolation on (assert shared checkout clean before integration, commit lands).
  (b) one carrier pending: agent called and item graduates as today.
  (c) every carrier retired (superseded/): NOT closed, dispatched as today.
  (d) one executed and one superseded carrier: NOT closed.
  (e) one executed IPD carrier plus an approved (not implemented) spec carrier: NOT closed.
  (f) Blocks-Release: rel001 item whose executed carrier carries the same gate: closed through predicate.
  (g) Blocks-Release item whose executed carrier carries NO gate: not closed, agent never called, queue fail-gate with needs_input=True.
  (h) backlog_graduate_count returns no finding for (a)'s tree and still refuses an item with zero carriers that produced nothing.
  (i) post-turn route of E-04 (b): fake agent invoked, item becomes complete during turn, ends in done/, never graduated/.
"""

from __future__ import annotations

import contextlib
import io
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from agent_workflows import (
    production_checks,
    runner_shared,
)
from tests.test_backlog_production import (
    _HOSTS,
    _make_test_repo,
    _patch_host_agent,
    _write_backlog_item,
    _write_conforming_plan,
)


def _write_spec_item(
    repo: Path,
    *,
    id6: str,
    status: str = "approved",
    backlog_id6: str | None = None,
    gate: str | None = None,
) -> Path:
    spc_dir = repo / ".aw" / "records" / "specs" / status
    spc_dir.mkdir(parents=True, exist_ok=True)
    f_path = spc_dir / f"20260901-{id6}-01-{id6}-test.spec.md"
    bkl_line = f"- From-Backlog: {backlog_id6}\n" if backlog_id6 else ""
    gate_line = f"- Blocks-Release: {gate}\n" if gate else ""
    f_path.write_text(
        f"""# SPEC: Test Spec {id6}
- Id: {id6}
- Status: {status}
{bkl_line}{gate_line}
## Workflow history
- 2026-09-01 {status} (tester): created.
""",
        encoding="utf-8",
    )
    return f_path


class TestBacklogAlreadyCompleteUnitE02(unittest.TestCase):
    """Direct unit tests for backlog_item_already_complete predicate (E-02, V-02)."""

    def test_predicate_states(self):
        with tempfile.TemporaryDirectory() as td:
            repo = _make_test_repo(Path(td))

            # 1. Item with only executed IPD carriers -> COMPLETE
            _write_backlog_item(repo, id6="bklcmp", status="open")
            _write_conforming_plan(
                repo, id6="plnc01", backlog_id6="bklcmp", bucket="executed"
            )
            res_cmp = runner_shared.backlog_item_already_complete(repo, "bklcmp")
            self.assertEqual(res_cmp.status, "COMPLETE")
            self.assertTrue(res_cmp.is_complete)
            self.assertIsNotNone(res_cmp.evidence)
            self.assertTrue(any("plnc01" in c for c in res_cmp.carriers))

            # 2. Item with one pending carrier -> NOT_COMPLETE
            _write_backlog_item(repo, id6="bklpnd", status="open")
            _write_conforming_plan(
                repo, id6="plnp01", backlog_id6="bklpnd", bucket="pending"
            )
            res_pnd = runner_shared.backlog_item_already_complete(repo, "bklpnd")
            self.assertEqual(res_pnd.status, "NOT_COMPLETE")
            self.assertFalse(res_pnd.is_complete)
            self.assertIn("IPD carrier(s) not executed", res_pnd.reason)

            # 3. Item with all carriers retired (superseded) -> NOT_COMPLETE
            _write_backlog_item(repo, id6="bklret", status="open")
            _write_conforming_plan(
                repo, id6="plnr01", backlog_id6="bklret", bucket="superseded"
            )
            res_ret = runner_shared.backlog_item_already_complete(repo, "bklret")
            self.assertEqual(res_ret.status, "NOT_COMPLETE")
            self.assertFalse(res_ret.is_complete)
            self.assertIn("IPD carrier(s) not executed", res_ret.reason)

            # 4. Item with mixed executed and superseded carriers -> NOT_COMPLETE
            _write_backlog_item(repo, id6="bklmix", status="open")
            _write_conforming_plan(
                repo, id6="plnm01", backlog_id6="bklmix", bucket="executed"
            )
            _write_conforming_plan(
                repo, id6="plnm02", backlog_id6="bklmix", bucket="superseded"
            )
            res_mix = runner_shared.backlog_item_already_complete(repo, "bklmix")
            self.assertEqual(res_mix.status, "NOT_COMPLETE")
            self.assertFalse(res_mix.is_complete)
            self.assertIn("IPD carrier(s) not executed", res_mix.reason)

            # 5. Item with executed IPD plus approved (not implemented) spec carrier -> NOT_COMPLETE
            _write_backlog_item(repo, id6="bklspc", status="open")
            _write_conforming_plan(
                repo, id6="plns01", backlog_id6="bklspc", bucket="executed"
            )
            _write_spec_item(
                repo, id6="spc001", status="approved", backlog_id6="bklspc"
            )
            res_spc = runner_shared.backlog_item_already_complete(repo, "bklspc")
            self.assertEqual(res_spc.status, "NOT_COMPLETE")
            self.assertFalse(res_spc.is_complete)
            self.assertIn("spec carrier(s) not implemented", res_spc.reason)

            # 6. Item with only non-IPD carriers (spec only) -> NO_IPD_CARRIER
            _write_backlog_item(repo, id6="bklnoipd", status="open")
            _write_spec_item(
                repo, id6="spc002", status="implemented", backlog_id6="bklnoipd"
            )
            res_noipd = runner_shared.backlog_item_already_complete(repo, "bklnoipd")
            self.assertEqual(res_noipd.status, "NO_IPD_CARRIER")
            self.assertFalse(res_noipd.is_complete)

            # 7. Item with no carriers at all -> NO_IPD_CARRIER
            _write_backlog_item(repo, id6="bklnone", status="open")
            res_none = runner_shared.backlog_item_already_complete(repo, "bklnone")
            self.assertEqual(res_none.status, "NO_IPD_CARRIER")
            self.assertFalse(res_none.is_complete)


class TestBacklogAlreadyCompleteIntegrationE05(unittest.TestCase):
    """Spec runner integration matrix on both hosts (E-05)."""

    def test_case_a_no_isolate_worktree(self):
        """Case (a): every IPD carrier executed; item closed done, agent never called,
        backlog-already-complete event present, queue executed (no-isolate-worktree mode).
        """
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    _write_backlog_item(repo, id6="bkla01", status="open")
                    _write_conforming_plan(
                        repo, id6="plna01", backlog_id6="bkla01", bucket="executed"
                    )
                    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
                    subprocess.run(
                        ["git", "commit", "-qm", "setup fixtures"],
                        cwd=repo,
                        check=True,
                    )

                    run_id = f"run-{host_label}-case-a-nois"
                    cmd = [
                        "start",
                        "bkla01",
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

                    agent_calls = []

                    def fake_agent(*args, **kwargs):
                        agent_calls.append(args)
                        return 0, "session", run_dir / "log.txt", ["cmd"]

                    with _patch_host_agent(mod, fake_agent):
                        with contextlib.redirect_stdout(
                            buf
                        ), contextlib.redirect_stderr(buf):
                            mod.run_queue(run_dir, retry_incomplete=False)

                    # Agent should never be called
                    self.assertEqual(len(agent_calls), 0)

                    state = json.loads(
                        (run_dir / "state.json").read_text(encoding="utf-8")
                    )
                    item = state["queue"][0]
                    self.assertEqual(item["status"], "executed")
                    self.assertEqual(item["attempts"][0]["disposition"], "executed")

                    # Backlog item must be in done/
                    bkl_files = list(
                        repo.glob(".aw/records/backlog/**/2026*bkla01*.backlog.md")
                    )
                    self.assertEqual(len(bkl_files), 1)
                    self.assertIn("/done/", str(bkl_files[0]).replace("\\", "/"))
                    self.assertIn("- Status: done", bkl_files[0].read_text("utf-8"))

                    # backlog-already-complete event present
                    events = [
                        json.loads(line)
                        for line in (run_dir / "events.jsonl")
                        .read_text("utf-8")
                        .splitlines()
                        if line.strip()
                    ]
                    evt = [
                        e
                        for e in events
                        if e.get("event") == "backlog-already-complete"
                    ]
                    self.assertEqual(len(evt), 1)
                    self.assertEqual(evt[0]["id6"], "bkla01")
                    self.assertTrue(any("plna01" in c for c in evt[0]["carriers"]))

    def test_case_a_with_isolate_worktree(self):
        """Case (a) with isolation: shared checkout git status is empty before integration,
        close arrives on main as a commit, agent never called.
        """
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    _write_backlog_item(repo, id6="bkla02", status="open")
                    _write_conforming_plan(
                        repo, id6="plna02", backlog_id6="bkla02", bucket="executed"
                    )
                    (repo / ".gitignore").write_text(
                        ".aw/state/\n.aw/records/runs/\n.aw/worktrees/\n",
                        encoding="utf-8",
                    )
                    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
                    subprocess.run(
                        ["git", "commit", "-qm", "setup fixtures"],
                        cwd=repo,
                        check=True,
                    )

                    head_before = subprocess.check_output(
                        ["git", "rev-parse", "HEAD"], cwd=repo, text=True
                    ).strip()

                    run_id = f"run-{host_label}-case-a-is"
                    cmd = [
                        "start",
                        "bkla02",
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

                    agent_calls = []

                    def fake_agent(*args, **kwargs):
                        agent_calls.append(args)
                        return 0, "session", run_dir / "log.txt", ["cmd"]

                    status_before_integration = []
                    real_integrate = mod.integrate_review_lane_branch

                    def spy_integrate(r, handle, id6_arg):
                        st = subprocess.check_output(
                            ["git", "status", "--porcelain"], cwd=r, text=True
                        ).strip()
                        status_before_integration.append(st)
                        return real_integrate(r, handle, id6_arg)

                    with _patch_host_agent(mod, fake_agent), mock.patch.object(
                        mod, "integrate_review_lane_branch", spy_integrate
                    ):
                        with contextlib.redirect_stdout(
                            buf
                        ), contextlib.redirect_stderr(buf):
                            mod.run_queue(run_dir, retry_incomplete=False)

                    # Agent should never be called
                    self.assertEqual(len(agent_calls), 0)

                    # Shared checkout porcelain status was clean before integration
                    self.assertEqual(len(status_before_integration), 1)
                    self.assertEqual(status_before_integration[0], "")

                    # Head moved forward with commit on main
                    head_after = subprocess.check_output(
                        ["git", "rev-parse", "HEAD"], cwd=repo, text=True
                    ).strip()
                    self.assertNotEqual(head_before, head_after)

                    # Backlog item must be in done/ on main
                    bkl_files = list(
                        repo.glob(".aw/records/backlog/**/2026*bkla02*.backlog.md")
                    )
                    self.assertEqual(len(bkl_files), 1)
                    self.assertIn("/done/", str(bkl_files[0]).replace("\\", "/"))

    def test_case_b_one_carrier_pending(self):
        """Case (b): one carrier pending: agent called and item graduates as today."""
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    _write_backlog_item(repo, id6="bklb01", status="open")
                    _write_conforming_plan(
                        repo, id6="plnb01", backlog_id6="bklb01", bucket="pending"
                    )
                    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
                    subprocess.run(
                        ["git", "commit", "-qm", "setup fixtures"],
                        cwd=repo,
                        check=True,
                    )

                    run_id = f"run-{host_label}-case-b"
                    cmd = [
                        "start",
                        "bklb01",
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

                    agent_calls = []

                    def fake_agent(
                        state, rdir, item, plan_path, prompt_path, attempt_no, **kwargs
                    ):
                        agent_calls.append(item["id6"])
                        # Write a conforming plan so graduation succeeds
                        work_dir = kwargs.get("work_dir")
                        target = Path(work_dir) if work_dir else Path(state["repo"])
                        _write_conforming_plan(
                            target, id6="plnb02", backlog_id6="bklb01"
                        )
                        return 0, "session", rdir / "log.txt", ["cmd"]

                    with _patch_host_agent(mod, fake_agent):
                        with contextlib.redirect_stdout(
                            buf
                        ), contextlib.redirect_stderr(buf):
                            mod.run_queue(run_dir, retry_incomplete=False)

                    # Agent WAS called
                    self.assertEqual(len(agent_calls), 1)

                    # Item graduated
                    bkl_files = list(
                        repo.glob(".aw/records/backlog/**/2026*bklb01*.backlog.md")
                    )
                    self.assertIn("/graduated/", str(bkl_files[0]).replace("\\", "/"))

    def test_case_c_every_carrier_retired(self):
        """Case (c): every carrier retired (superseded/): item NOT closed, dispatched as today."""
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    _write_backlog_item(repo, id6="bklc01", status="open")
                    _write_conforming_plan(
                        repo, id6="plnc01", backlog_id6="bklc01", bucket="superseded"
                    )
                    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
                    subprocess.run(
                        ["git", "commit", "-qm", "setup fixtures"],
                        cwd=repo,
                        check=True,
                    )

                    run_id = f"run-{host_label}-case-c"
                    cmd = [
                        "start",
                        "bklc01",
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

                    agent_calls = []

                    def fake_agent(state, rdir, item, *args, **kwargs):
                        agent_calls.append(item["id6"])
                        return 0, "session", rdir / "log.txt", ["cmd"]

                    with _patch_host_agent(mod, fake_agent):
                        with contextlib.redirect_stdout(
                            buf
                        ), contextlib.redirect_stderr(buf):
                            mod.run_queue(run_dir, retry_incomplete=False)

                    # Agent WAS called because item was not closed at dispatch
                    self.assertEqual(len(agent_calls), 1)

    def test_case_d_mixed_executed_and_superseded(self):
        """Case (d): one executed and one superseded carrier: NOT closed."""
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    _write_backlog_item(repo, id6="bkld01", status="open")
                    _write_conforming_plan(
                        repo, id6="plnd01", backlog_id6="bkld01", bucket="executed"
                    )
                    _write_conforming_plan(
                        repo, id6="plnd02", backlog_id6="bkld01", bucket="superseded"
                    )
                    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
                    subprocess.run(
                        ["git", "commit", "-qm", "setup fixtures"],
                        cwd=repo,
                        check=True,
                    )

                    run_id = f"run-{host_label}-case-d"
                    cmd = [
                        "start",
                        "bkld01",
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

                    agent_calls = []

                    def fake_agent(state, rdir, item, *args, **kwargs):
                        agent_calls.append(item["id6"])
                        return 0, "session", rdir / "log.txt", ["cmd"]

                    with _patch_host_agent(mod, fake_agent):
                        with contextlib.redirect_stdout(
                            buf
                        ), contextlib.redirect_stderr(buf):
                            mod.run_queue(run_dir, retry_incomplete=False)

                    # Agent WAS called
                    self.assertEqual(len(agent_calls), 1)

    def test_case_e_executed_ipd_plus_approved_spec(self):
        """Case (e): one executed IPD carrier plus an approved (not implemented) spec carrier: NOT closed."""
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    _write_backlog_item(repo, id6="bkle01", status="open")
                    _write_conforming_plan(
                        repo, id6="plne01", backlog_id6="bkle01", bucket="executed"
                    )
                    _write_spec_item(
                        repo, id6="spce01", status="approved", backlog_id6="bkle01"
                    )
                    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
                    subprocess.run(
                        ["git", "commit", "-qm", "setup fixtures"],
                        cwd=repo,
                        check=True,
                    )

                    run_id = f"run-{host_label}-case-e"
                    cmd = [
                        "start",
                        "bkle01",
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

                    agent_calls = []

                    def fake_agent(state, rdir, item, *args, **kwargs):
                        agent_calls.append(item["id6"])
                        return 0, "session", rdir / "log.txt", ["cmd"]

                    with _patch_host_agent(mod, fake_agent):
                        with contextlib.redirect_stdout(
                            buf
                        ), contextlib.redirect_stderr(buf):
                            mod.run_queue(run_dir, retry_incomplete=False)

                    # Agent WAS called
                    self.assertEqual(len(agent_calls), 1)

    def test_case_f_gated_item_matching_gate(self):
        """Case (f): Blocks-Release: rel001 item whose executed carrier carries the same gate:
        closed through the predicate.
        """
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    _write_backlog_item(
                        repo, id6="bklf01", status="open", gate="rel001"
                    )
                    _write_conforming_plan(
                        repo,
                        id6="plnf01",
                        backlog_id6="bklf01",
                        bucket="executed",
                        gate="rel001",
                    )
                    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
                    subprocess.run(
                        ["git", "commit", "-qm", "setup fixtures"],
                        cwd=repo,
                        check=True,
                    )

                    run_id = f"run-{host_label}-case-f"
                    cmd = [
                        "start",
                        "bklf01",
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

                    agent_calls = []

                    def fake_agent(*args, **kwargs):
                        agent_calls.append(args)
                        return 0, "session", run_dir / "log.txt", ["cmd"]

                    with _patch_host_agent(mod, fake_agent):
                        with contextlib.redirect_stdout(
                            buf
                        ), contextlib.redirect_stderr(buf):
                            mod.run_queue(run_dir, retry_incomplete=False)

                    # Agent should never be called
                    self.assertEqual(len(agent_calls), 0)

                    # Item closed done
                    bkl_files = list(
                        repo.glob(".aw/records/backlog/**/2026*bklf01*.backlog.md")
                    )
                    self.assertIn("/done/", str(bkl_files[0]).replace("\\", "/"))

    def test_case_g_gated_item_no_gate_on_carrier(self):
        """Case (g): Blocks-Release item whose executed carrier carries NO gate and no other
        route satisfies it: not closed, agent never called, queue fail-gate with needs_input=True.
        """
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    _write_backlog_item(
                        repo, id6="bklg01", status="open", gate="rel001"
                    )
                    # Carrier has NO gate
                    _write_conforming_plan(
                        repo,
                        id6="plng01",
                        backlog_id6="bklg01",
                        bucket="executed",
                        gate=None,
                    )
                    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
                    subprocess.run(
                        ["git", "commit", "-qm", "setup fixtures"],
                        cwd=repo,
                        check=True,
                    )

                    run_id = f"run-{host_label}-case-g"
                    cmd = [
                        "start",
                        "bklg01",
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

                    agent_calls = []

                    def fake_agent(*args, **kwargs):
                        agent_calls.append(args)
                        return 0, "session", run_dir / "log.txt", ["cmd"]

                    with _patch_host_agent(mod, fake_agent):
                        with contextlib.redirect_stdout(
                            buf
                        ), contextlib.redirect_stderr(buf):
                            mod.run_queue(run_dir, retry_incomplete=False)

                    # Agent should never be called
                    self.assertEqual(len(agent_calls), 0)

                    state = json.loads(
                        (run_dir / "state.json").read_text(encoding="utf-8")
                    )
                    item = state["queue"][0]
                    self.assertEqual(item["status"], "fail-gate")
                    self.assertTrue(item.get("needs_input"))
                    self.assertIn("refusal", item)

                    # Item file still in open/
                    bkl_files = list(
                        repo.glob(".aw/records/backlog/**/2026*bklg01*.backlog.md")
                    )
                    self.assertIn("/open/", str(bkl_files[0]).replace("\\", "/"))

    def test_case_h_backlog_graduate_count(self):
        """Case (h): backlog_graduate_count returns no finding for (a)'s tree and
        still refuses an item with zero carriers that produced nothing.
        """
        with tempfile.TemporaryDirectory() as td:
            repo = _make_test_repo(Path(td))

            # Tree (a): item with executed plan carrier, 0 new plans produced
            _write_backlog_item(repo, id6="bklh01", status="open")
            _write_conforming_plan(
                repo, id6="plnh01", backlog_id6="bklh01", bucket="executed"
            )
            findings_a = production_checks.backlog_graduate_count(
                repo, "bklh01", {"plnh01"}
            )
            self.assertEqual(findings_a, [])

            # Item with zero carriers that produced nothing -> refuses
            _write_backlog_item(repo, id6="bklh02", status="open")
            findings_zero = production_checks.backlog_graduate_count(
                repo, "bklh02", set()
            )
            self.assertEqual(len(findings_zero), 1)
            self.assertEqual(findings_zero[0][0], "BACKLOG-GRADUATE-COUNT")
            self.assertIn("produced 0 linked IPDs", findings_zero[0][2])

    def test_case_i_post_turn_route(self):
        """Case (i): post-turn route of E-04 (b): item becomes COMPLETE during turn,
        ends in done/, never graduated/.
        """
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    _write_backlog_item(repo, id6="bkli01", status="open")
                    # Starts pending, so dispatch check sees NOT_COMPLETE
                    p_path = _write_conforming_plan(
                        repo, id6="plni01", backlog_id6="bkli01", bucket="pending"
                    )
                    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
                    subprocess.run(
                        ["git", "commit", "-qm", "setup fixtures"],
                        cwd=repo,
                        check=True,
                    )

                    run_id = f"run-{host_label}-case-i"
                    cmd = [
                        "start",
                        "bkli01",
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
                        # Carrier becomes executed during turn (e.g. concurrent or completed carrier move)
                        exec_dir = repo / ".aw" / "records" / "plans" / "executed"
                        exec_dir.mkdir(parents=True, exist_ok=True)
                        dest = exec_dir / p_path.name
                        shutil.move(str(p_path), str(dest))
                        subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
                        subprocess.run(
                            ["git", "commit", "-qm", "carrier executed"],
                            cwd=repo,
                            check=True,
                        )
                        # Produced 0 new plans
                        return 0, "session", rdir / "log.txt", ["cmd"]

                    with _patch_host_agent(mod, fake_agent):
                        with contextlib.redirect_stdout(
                            buf
                        ), contextlib.redirect_stderr(buf):
                            mod.run_queue(run_dir, retry_incomplete=False)

                    # Item must end in done/, never graduated/
                    bkl_files = list(
                        repo.glob(".aw/records/backlog/**/2026*bkli01*.backlog.md")
                    )
                    self.assertEqual(len(bkl_files), 1)
                    self.assertIn("/done/", str(bkl_files[0]).replace("\\", "/"))
                    self.assertNotIn(
                        "/graduated/", str(bkl_files[0]).replace("\\", "/")
                    )
