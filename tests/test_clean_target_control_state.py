"""Outcome tests for clean-target control state and isolated worktrees (IPD qk0ew6).

Validates that:
(a) E-02 path table from root and external lane under clean-delta (completely-clean-target
    and local-only): checkout_control_root and clean_delta_control_root return
    <AW_HOME>/projects/<id>, control / "state" == logical_roots["state"],
    run-record root == state_root, and non-git / bare / tracked fallbacks return baseline;
(b) E-03 is_main_checkout returns True for main checkouts and False for linked lanes;
(c) E-04 allocate_worktree creates lanes under <AW_HOME>/projects/<id>/worktrees/<name>,
    stores owner records under <AW_HOME>/projects/<id>/worktrees/.owners/, aw lanes list --json
    reports it, and teardown cleans it up;
(d) E-05 lane self-ignore writes <lane>/.aw/.gitignore containing '*' on fresh and adopted lanes,
    snapshot_lane_dirty_work returns None, inspect_lane is LANE_EMPTY, and inventory_lane
    reports .aw/.gitignore only under unknown_ignored;
(e) E-06 control_state_dir routes work_cmd, checkup_dir and suite_baseline_checkout_path under
    <AW_HOME>/projects/<id>/state/, and checkup.run_checkup_cli outputs a relativized 'Saved record:'
    prefixed <project home>/ with no absolute machine paths;
(f) E-07 path heuristics in render_stream._relativize_path and runner_shared.lane_worktree_display
    behave correctly, and oc_runipd._apply_execution_profile refuses the hardened profile for clean-delta;
(g) Inner aw from an external lane resolves the main project's project_id, receipt_dir,
    finalize_lock_path, state_root, and runs_repo_root;
(h) The acceptance bar: target repository git status --porcelain --ignored is empty and HEAD is unchanged
    after receipts, leases, owner records, and lane creation/teardown;
(i) Tracked control: all operations on tracked private-target fixture match baseline paths byte-identically.
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from agent_workflows import (
    checkup,
    ipd_lifecycle,
    render_stream,
    runner_shared,
    work_cmd,
    worktree_lease,
)
from agent_workflows.host_sandbox_profile import (
    SandboxProfileError,
)
from agent_workflows.oc_runipd import _apply_execution_profile
from agent_workflows.project_context import (
    resolve_project_context,
)


class TestCleanTargetControlState(unittest.TestCase):
    def setUp(self) -> None:
        ipd_lifecycle.clear_checkout_control_root_cache()
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name).resolve()

        self.fake_home = self.base / "home"
        self.fake_home.mkdir()
        self.fake_aw_home = self.fake_home / ".aw"
        self.fake_aw_home.mkdir()
        self.fake_xdg = self.fake_home / ".config"
        self.fake_xdg.mkdir()

        self.repo_root = Path(__file__).resolve().parent.parent

        self._orig_env = dict(os.environ)
        os.environ["HOME"] = str(self.fake_home)
        os.environ["AW_HOME"] = str(self.fake_aw_home)
        os.environ["XDG_CONFIG_HOME"] = str(self.fake_xdg)
        os.environ["AW_NO_REEXEC"] = "1"
        os.environ["PYTHONPATH"] = (
            f"{self.repo_root}:{os.environ.get('PYTHONPATH', '')}"
        )
        os.environ.pop("AW_CONFIG_DIR", None)
        os.environ["GIT_AUTHOR_NAME"] = "Test User"
        os.environ["GIT_AUTHOR_EMAIL"] = "test@example.com"
        os.environ["GIT_COMMITTER_NAME"] = "Test User"
        os.environ["GIT_COMMITTER_EMAIL"] = "test@example.com"

        self.env = dict(os.environ)

        # 1. Set up completely-clean-target fixture
        self.clean_repo = self.base / "clean_repo"
        self.pre_clean_sha = self._init_git_repo(self.clean_repo)
        self._run_aw_install(self.clean_repo, "completely-clean-target")
        self._strip_in_target_residue(self.clean_repo, self.pre_clean_sha)

        # Verify acceptance prerequisite: target is completely clean before cases run
        pre_status = subprocess.check_output(
            ["git", "-C", str(self.clean_repo), "status", "--porcelain", "--ignored"],
            env=self.env,
            text=True,
        )
        self.assertEqual(
            pre_status, "", "clean_repo must be completely clean before tests run"
        )

        ctx_clean = resolve_project_context(
            target_repo=str(self.clean_repo),
            aw_home=str(self.fake_aw_home),
            user_config_dir=str(self.fake_xdg / "agent-workflows"),
        )
        self.clean_proj_id = ctx_clean.project_id
        self.clean_proj_dir = self.fake_aw_home / "projects" / self.clean_proj_id
        self.clean_lane = self.clean_proj_dir / "worktrees" / "abc123"
        self.clean_lane.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            [
                "git",
                "-C",
                str(self.clean_repo),
                "worktree",
                "add",
                "--detach",
                str(self.clean_lane),
            ],
            check=True,
            capture_output=True,
            env=self.env,
        )

        # 2. Set up local-only fixture
        self.local_repo = self.base / "local_repo"
        self.pre_local_sha = self._init_git_repo(self.local_repo)
        self._run_aw_install(self.local_repo, "local-only")
        self._strip_in_target_residue(self.local_repo, self.pre_local_sha)
        ctx_local = resolve_project_context(
            target_repo=str(self.local_repo),
            aw_home=str(self.fake_aw_home),
            user_config_dir=str(self.fake_xdg / "agent-workflows"),
        )
        self.local_proj_id = ctx_local.project_id
        self.local_proj_dir = self.fake_aw_home / "projects" / self.local_proj_id
        self.local_lane = self.local_proj_dir / "worktrees" / "loc123"
        self.local_lane.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            [
                "git",
                "-C",
                str(self.local_repo),
                "worktree",
                "add",
                "--detach",
                str(self.local_lane),
            ],
            check=True,
            capture_output=True,
            env=self.env,
        )

        # 3. Set up tracked private-target control fixture
        self.tracked_repo = self.base / "tracked_repo"
        self.pre_tracked_sha = self._init_git_repo(self.tracked_repo)
        self._run_aw_install(self.tracked_repo, "private-target")
        self.tracked_lane = self.tracked_repo / ".aw" / "worktrees" / "trlane"
        self.tracked_lane.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            [
                "git",
                "-C",
                str(self.tracked_repo),
                "worktree",
                "add",
                str(self.tracked_lane),
            ],
            check=True,
            capture_output=True,
            env=self.env,
        )

    def tearDown(self) -> None:
        ipd_lifecycle.clear_checkout_control_root_cache()
        os.environ.clear()
        os.environ.update(self._orig_env)
        self.tmp.cleanup()

    def _init_git_repo(self, path: Path) -> str:
        path.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            ["git", "init", "-b", "main", str(path)],
            check=True,
            capture_output=True,
            env=self.env,
        )
        subprocess.run(
            ["git", "-C", str(path), "config", "user.name", "Test User"],
            check=True,
            env=self.env,
        )
        subprocess.run(
            ["git", "-C", str(path), "config", "user.email", "test@example.com"],
            check=True,
            env=self.env,
        )
        (path / "README.md").write_text("# Test Repo\n", encoding="utf-8")
        subprocess.run(
            ["git", "-C", str(path), "add", "README.md"], check=True, env=self.env
        )
        subprocess.run(
            ["git", "-C", str(path), "commit", "-m", "Initial commit"],
            check=True,
            capture_output=True,
            env=self.env,
        )
        return subprocess.check_output(
            ["git", "-C", str(path), "rev-parse", "HEAD"], env=self.env, text=True
        ).strip()

    def _run_aw_install(self, path: Path, preset: str) -> None:
        cmd = [
            sys.executable,
            "-m",
            "agent_workflows",
            "install",
            str(path),
            "--preset",
            preset,
            "-y",
            "--no-interactive",
        ]
        subprocess.run(cmd, check=True, capture_output=True, env=self.env)

    def _strip_in_target_residue(self, path: Path, pre_sha: str) -> None:
        # E-08 recipe: remove in-target residue from HEAD, the index AND the working tree
        subprocess.run(
            ["git", "-C", str(path), "reset", "-q", "--hard", pre_sha],
            check=True,
            env=self.env,
        )
        subprocess.run(
            ["git", "-C", str(path), "clean", "-fdxq"], check=True, env=self.env
        )

    def test_a_e02_path_table(self) -> None:
        """(a) Path table from root and external lane for clean-delta repositories."""
        for label, repo, proj_dir, lane in [
            (
                "completely-clean-target",
                self.clean_repo,
                self.clean_proj_dir,
                self.clean_lane,
            ),
            ("local-only", self.local_repo, self.local_proj_dir, self.local_lane),
        ]:
            with self.subTest(preset=label):
                self.assertEqual(ipd_lifecycle.checkout_control_root(repo), proj_dir)
                self.assertEqual(ipd_lifecycle.clean_delta_control_root(repo), proj_dir)
                self.assertEqual(ipd_lifecycle.checkout_control_root(lane), proj_dir)
                self.assertEqual(ipd_lifecycle.clean_delta_control_root(lane), proj_dir)

                ctx = resolve_project_context(
                    target_repo=str(repo),
                    aw_home=str(self.fake_aw_home),
                    user_config_dir=str(self.fake_xdg / "agent-workflows"),
                )
                state_logical = Path(ctx.logical_roots["state"])
                self.assertEqual(
                    ipd_lifecycle.checkout_control_root(repo) / "state", state_logical
                )
                self.assertEqual(
                    ipd_lifecycle.checkout_control_root(repo) / "records" / "runs",
                    runner_shared.state_root(repo),
                )

        # Negative / fallback cases
        # Non-git directory
        non_git = self.base / "non_git"
        non_git.mkdir()
        self.assertIsNone(ipd_lifecycle.clean_delta_control_root(non_git))
        self.assertEqual(ipd_lifecycle.checkout_control_root(non_git), non_git / ".aw")

        # Bare repo
        bare_repo = self.base / "bare.git"
        subprocess.run(
            ["git", "init", "--bare", str(bare_repo)],
            check=True,
            capture_output=True,
            env=self.env,
        )
        self.assertIsNone(ipd_lifecycle.clean_delta_control_root(bare_repo))
        self.assertEqual(
            ipd_lifecycle.checkout_control_root(bare_repo), bare_repo / ".aw"
        )

        # Tracked fixture
        self.assertIsNone(ipd_lifecycle.clean_delta_control_root(self.tracked_repo))
        self.assertEqual(
            ipd_lifecycle.checkout_control_root(self.tracked_repo),
            self.tracked_repo / ".aw",
        )

    def test_b_e03_is_main_checkout(self) -> None:
        """(b) is_main_checkout derives main worktree from common dir."""
        self.assertTrue(ipd_lifecycle.is_main_checkout(self.clean_repo))
        self.assertFalse(ipd_lifecycle.is_main_checkout(self.clean_lane))
        self.assertTrue(ipd_lifecycle.is_main_checkout(self.tracked_repo))
        self.assertFalse(ipd_lifecycle.is_main_checkout(self.tracked_lane))

        non_git = self.base / "non_git_b"
        non_git.mkdir()
        self.assertFalse(ipd_lifecycle.is_main_checkout(non_git))

        bare_repo = self.base / "bare_b.git"
        subprocess.run(
            ["git", "init", "--bare", str(bare_repo)],
            check=True,
            capture_output=True,
            env=self.env,
        )
        self.assertFalse(ipd_lifecycle.is_main_checkout(bare_repo))

    def test_c_e04_allocate_worktree_and_lanes_cli(self) -> None:
        """(c) allocate_worktree location, owner record, aw lanes list --json, teardown."""
        handle = worktree_lease.allocate_worktree(self.clean_repo, "wtc04")
        expected_path = self.clean_proj_dir / "worktrees" / "wtc04"
        expected_owner = self.clean_proj_dir / "worktrees" / ".owners" / "wtc04.json"

        self.assertEqual(handle.path, expected_path)
        self.assertEqual(
            worktree_lease._owner_record_path(self.clean_repo, "wtc04"), expected_owner
        )
        self.assertTrue(expected_owner.exists())
        self.assertTrue(handle.path.exists())

        # Subprocess aw lanes list --json
        cmd = [sys.executable, "-m", "agent_workflows", "lanes", "list", "--json"]
        out = subprocess.check_output(cmd, cwd=self.clean_repo, env=self.env, text=True)
        data = json.loads(out)
        lanes = data.get("lanes", [])
        lane_ids = [row.get("lane") for row in lanes]
        self.assertIn("wtc04", lane_ids)

        # Teardown
        worktree_lease.teardown_worktree(self.clean_repo, handle)
        self.assertFalse(handle.path.exists())

    def test_d_e05_lane_self_ignore(self) -> None:
        """(d) Lane self-ignore on fresh and adopted clean-delta lanes, and tracked lane control."""
        from agent_workflows import lane_containment

        # 1. Fresh lane
        handle = worktree_lease.allocate_worktree(self.clean_repo, "ign05")
        ign_file = handle.path / ".aw" / ".gitignore"
        self.assertTrue(ign_file.exists())
        self.assertEqual(ign_file.read_text(encoding="utf-8").strip(), "*")

        # Create scratch inside lane
        scratch_dir = handle.path / ".aw" / "lane-scratch"
        scratch_dir.mkdir(parents=True, exist_ok=True)
        (scratch_dir / "y").write_text("scratch", encoding="utf-8")
        state_dir = handle.path / ".aw" / "state"
        state_dir.mkdir(parents=True, exist_ok=True)
        (state_dir / "x").write_text("state", encoding="utf-8")

        # Status inside lane must be empty
        lane_status = subprocess.check_output(
            ["git", "-C", str(handle.path), "status", "--porcelain"],
            env=self.env,
            text=True,
        )
        self.assertEqual(lane_status.strip(), "")

        # snapshot_lane_dirty_work must return None
        self.assertIsNone(
            worktree_lease.snapshot_lane_dirty_work(self.clean_repo, handle)
        )

        # inspect_lane must report LANE_EMPTY
        insp = worktree_lease.inspect_lane(self.clean_repo, "ign05")
        self.assertEqual(insp.state, worktree_lease.LANE_EMPTY)

        # inventory_lane must report .aw/.gitignore in unknown_ignored and unknown empty
        inv = lane_containment.inventory_lane(
            lane_root=handle.path, branch=handle.branch
        )
        self.assertEqual(len(inv.unknown), 0)
        self.assertIn(".aw/.gitignore", inv.unknown_ignored)

        worktree_lease.teardown_worktree(self.clean_repo, handle)

        # 2. Adopted lane (pre-existing empty lane without .aw/.gitignore)
        adp_path = self.clean_proj_dir / "worktrees" / "adp05"
        subprocess.run(
            [
                "git",
                "-C",
                str(self.clean_repo),
                "worktree",
                "add",
                "-b",
                "aw/lane/adp05",
                str(adp_path),
            ],
            check=True,
            capture_output=True,
            env=self.env,
        )
        self.assertFalse((adp_path / ".aw" / ".gitignore").exists())

        handle_adp = worktree_lease.allocate_worktree(
            self.clean_repo, "adp05", allow_adopt=True
        )
        self.assertEqual(handle_adp.disposition, worktree_lease.DISPOSITION_ADOPTED)
        self.assertTrue((adp_path / ".aw" / ".gitignore").exists())
        self.assertEqual(
            (adp_path / ".aw" / ".gitignore").read_text(encoding="utf-8").strip(), "*"
        )

        worktree_lease.teardown_worktree(self.clean_repo, handle_adp)

        # 3. Tracked mode lane must NOT get the clean-delta '*' ignore file
        handle_tr = worktree_lease.allocate_worktree(self.tracked_repo, "trign05")
        tr_ign = handle_tr.path / ".aw" / ".gitignore"
        if tr_ign.exists():
            self.assertNotEqual(tr_ign.read_text(encoding="utf-8").strip(), "*")
        worktree_lease.teardown_worktree(self.tracked_repo, handle_tr)

        # In a plain git repo without tracked .aw, no .aw/.gitignore is written
        plain_repo = self.base / "plain_repo"
        self._init_git_repo(plain_repo)
        handle_plain = worktree_lease.allocate_worktree(plain_repo, "plain05")
        self.assertFalse((handle_plain.path / ".aw" / ".gitignore").exists())
        worktree_lease.teardown_worktree(plain_repo, handle_plain)

    def test_e_e06_control_state_paths_and_checkup(self) -> None:
        """(e) E-06 control_state_dir paths and checkup Saved record relativization."""
        import argparse

        # Clean delta accessors
        self.assertEqual(
            work_cmd._work_dir(self.clean_repo, "p06"),
            self.clean_proj_dir / "state" / "work" / "p06",
        )
        self.assertEqual(
            work_cmd._work_dir(self.clean_lane, "p06"),
            self.clean_proj_dir / "state" / "work" / "p06",
        )
        self.assertEqual(
            checkup.checkup_dir(self.clean_repo),
            self.clean_proj_dir / "state" / "checkup",
        )
        self.assertEqual(
            checkup.checkup_dir(self.clean_lane),
            self.clean_proj_dir / "state" / "checkup",
        )
        self.assertEqual(
            runner_shared.suite_baseline_checkout_path(self.clean_repo, "x1y2z3", 1),
            self.clean_proj_dir / "state" / "suite-baselines" / "x1y2z3-attempt1",
        )
        self.assertEqual(
            runner_shared.suite_baseline_checkout_path(self.clean_lane, "x1y2z3", 1),
            self.clean_proj_dir / "state" / "suite-baselines" / "x1y2z3-attempt1",
        )

        # In-process checkup run
        orig_perform = checkup.perform_checkup
        try:
            checkup.perform_checkup = lambda *args, **kwargs: {
                "ci": {"status": "PASSING"},
                "slow_checks": {},
            }
            buf = io.StringIO()
            cli_args = argparse.Namespace(
                dir=str(self.clean_repo), agent=False, json=False
            )
            with contextlib.redirect_stdout(buf):
                rc = checkup.run_checkup_cli(cli_args)
            self.assertEqual(rc, 0)
            out = buf.getvalue()
            saved_lines = [
                line_item
                for line_item in out.splitlines()
                if "Saved record:" in line_item
            ]
            self.assertEqual(len(saved_lines), 1)
            saved_line = saved_lines[0]
            self.assertTrue(
                "Saved record: <project home>/state/checkup/last.json" in saved_line
                or "Saved record: <project home>/state\\checkup\\last.json"
                in saved_line
            )
            # Must not contain absolute machine paths
            self.assertNotIn(str(self.fake_aw_home), saved_line)
            self.assertNotIn(str(self.base), saved_line)
        finally:
            checkup.perform_checkup = orig_perform

    def test_f_e07_heuristics_and_hardened_refusal(self) -> None:
        """(f) Path heuristics in render_stream/runner_shared and hardened profile refusal."""
        # 1. render_stream._relativize_path
        ext_path = str(self.clean_lane / "src" / "feature.py")
        rel_ext = render_stream._relativize_path(
            ext_path, repo_root=self.clean_repo, work_dir=self.clean_lane
        )
        self.assertEqual(rel_ext, "src/feature.py")

        in_repo_lane = self.tracked_repo / ".aw" / "worktrees" / "trlane"
        in_path = str(in_repo_lane / "src" / "feature.py")
        rel_in = render_stream._relativize_path(
            in_path, repo_root=self.tracked_repo, work_dir=in_repo_lane
        )
        self.assertEqual(rel_in, ".aw/worktrees/trlane/src/feature.py")

        # 2. runner_shared.lane_worktree_display
        self.assertIsNone(
            runner_shared.lane_worktree_display(self.clean_repo, self.clean_lane)
        )
        self.assertEqual(
            runner_shared.lane_worktree_display(self.tracked_repo, self.tracked_lane),
            ".aw/worktrees/trlane",
        )

        # 3. Hardened profile refusal for clean-delta
        state = {
            "options": {"execution_profile": "hardened"},
            "repo": str(self.clean_repo),
            "run_id": "testrun",
            "host_capabilities": {
                "descriptor": {"supports_os_sandbox": True},
                "supports_os_sandbox": True,
            },
        }
        item = {"id6": "it0001"}
        with self.assertRaises(SandboxProfileError) as cm:
            _apply_execution_profile(
                state,
                item,
                ["cmd"],
                "opencode",
                str(self.clean_lane),
            )
        err_msg = str(cm.exception)
        self.assertIn(
            "the hardened execution profile is not supported for clean-delta repositories",
            err_msg,
        )
        self.assertIn("<AW_HOME>/projects/<id>/{config,system,records}", err_msg)

        # Lane scratch must NOT have been created
        lane_scratch = self.clean_lane / ".aw" / "lane-scratch" / "testrun" / "it0001"
        self.assertFalse(lane_scratch.exists())

        # Default profile returns argv unchanged
        state_def = dict(state, options={"execution_profile": "default"})
        argv_out = _apply_execution_profile(
            state_def,
            item,
            ["cmd", "arg"],
            "opencode",
            str(self.clean_lane),
        )
        self.assertEqual(argv_out, ["cmd", "arg"])

    def test_g_inner_aw_from_external_lane(self) -> None:
        """(g) Inner aw invocation from external lane resolves main project."""
        from agent_workflows import attention

        # 1. Subprocess aw context --agent
        cmd = [sys.executable, "-m", "agent_workflows", "context", "--agent"]
        out = subprocess.check_output(cmd, cwd=self.clean_lane, env=self.env, text=True)
        data = json.loads(out)
        self.assertEqual(data.get("outcome"), "clean")
        evidence = data.get("evidence", [])
        self.assertTrue(
            any(f"project_id:{self.clean_proj_id}" in str(e) for e in evidence),
            f"Expected project_id:{self.clean_proj_id} in evidence: {evidence}",
        )

        # 2. Subprocess python3 -c path accessors from cwd = lane
        code = (
            "import sys, os; from pathlib import Path; "
            "import agent_workflows.ipd_lifecycle as il, agent_workflows.runner_shared as rs, agent_workflows.attention as att; "
            "cwd = Path.cwd(); "
            "print('RECEIPT:' + str(il.receipt_dir(cwd))); "
            "print('LOCK:' + str(il.finalize_lock_path(cwd))); "
            "print('STATE_ROOT:' + str(rs.state_root(None))); "
            "print('RUNS_REPO:' + str(rs.runs_repo_root(cwd)))"
        )
        out2 = subprocess.check_output(
            [sys.executable, "-c", code], cwd=self.clean_lane, env=self.env, text=True
        )
        lines = dict(
            line.split(":", 1) for line in out2.strip().splitlines() if ":" in line
        )

        self.assertEqual(
            Path(lines["RECEIPT"]), self.clean_proj_dir / "state" / "ipd-lifecycle"
        )
        self.assertEqual(
            Path(lines["LOCK"]),
            self.clean_proj_dir
            / "state"
            / "runtime"
            / "locks"
            / "ipd_finalize_writer.lock",
        )
        self.assertEqual(
            Path(lines["RECEIPT"]), ipd_lifecycle.receipt_dir(self.clean_repo)
        )
        self.assertEqual(
            Path(lines["LOCK"]), ipd_lifecycle.finalize_lock_path(self.clean_repo)
        )
        self.assertEqual(
            Path(lines["STATE_ROOT"]), runner_shared.state_root(self.clean_repo)
        )
        self.assertEqual(
            Path(lines["RUNS_REPO"]).resolve(),
            runner_shared.runs_repo_root(self.clean_repo).resolve(),
        )

        # 3. attention._resolve_runs_repo_root(lane) returns main repo
        self.assertEqual(
            attention._resolve_runs_repo_root(self.clean_lane).resolve(),
            self.clean_repo.resolve(),
        )

    def test_h_acceptance_bar(self) -> None:
        """(h) Target repository git status --porcelain --ignored is empty and HEAD unchanged after operations."""
        # Perform lifecycle writes, leases, owner records, lane allocation and teardown
        rcpt_file = ipd_lifecycle.receipt_path_for(self.clean_repo, "acc001")
        rcpt_file.parent.mkdir(parents=True, exist_ok=True)
        rcpt_file.write_text("{}", encoding="utf-8")

        lease_file = work_cmd._lease_path(self.clean_repo, "acc001")
        lease_file.parent.mkdir(parents=True, exist_ok=True)
        lease_file.write_text("{}", encoding="utf-8")

        evidence_file = work_cmd._evidence_path(self.clean_repo, "acc001")
        evidence_file.parent.mkdir(parents=True, exist_ok=True)
        evidence_file.write_text("{}", encoding="utf-8")

        handle = worktree_lease.allocate_worktree(self.clean_repo, "acc001")
        self.assertTrue(handle.path.is_relative_to(self.clean_proj_dir))
        status_during = subprocess.check_output(
            ["git", "-C", str(self.clean_repo), "status", "--porcelain", "--ignored"],
            env=self.env,
            text=True,
        )
        self.assertEqual(
            status_during,
            "",
            f"Target repo dirty during lane existence:\n{status_during}",
        )
        worktree_lease.write_lane_owner(self.clean_repo, "acc001")
        worktree_lease.teardown_worktree(self.clean_repo, handle)

        # Check that receipts, leases and owner records were written under clean_proj_dir
        self.assertTrue(rcpt_file.is_relative_to(self.clean_proj_dir))
        self.assertTrue(lease_file.is_relative_to(self.clean_proj_dir))

        # The acceptance bar: target repo git status must be empty and HEAD unchanged
        status = subprocess.check_output(
            ["git", "-C", str(self.clean_repo), "status", "--porcelain", "--ignored"],
            env=self.env,
            text=True,
        )
        self.assertEqual(
            status,
            "",
            f"Target repo must be completely clean, but got status:\n{status}",
        )

        head = subprocess.check_output(
            ["git", "-C", str(self.clean_repo), "rev-parse", "HEAD"],
            env=self.env,
            text=True,
        ).strip()
        self.assertEqual(head, self.pre_clean_sha)

    def test_i_tracked_control(self) -> None:
        """(i) Tracked fixture produces exactly baseline paths byte-identically."""
        from agent_workflows import attention

        repo = self.tracked_repo
        self.assertEqual(ipd_lifecycle.checkout_control_root(repo), repo / ".aw")
        self.assertIsNone(ipd_lifecycle.clean_delta_control_root(repo))
        self.assertEqual(
            ipd_lifecycle.receipt_dir(repo), repo / ".aw" / "state" / "ipd-lifecycle"
        )
        self.assertEqual(
            ipd_lifecycle.finalize_lock_path(repo),
            repo / ".aw" / "state" / "runtime" / "locks" / "ipd_finalize_writer.lock",
        )
        self.assertEqual(
            worktree_lease._owner_record_path(repo, "x1y2z3"),
            repo / ".aw" / "worktrees" / ".owners" / "x1y2z3.json",
        )
        self.assertEqual(
            work_cmd._work_dir(repo, "x1y2z3"),
            repo / ".aw" / "state" / "work" / "x1y2z3",
        )
        self.assertEqual(checkup.checkup_dir(repo), repo / ".aw" / "state" / "checkup")
        self.assertEqual(
            runner_shared.suite_baseline_checkout_path(repo, "x1y2z3", 1),
            repo / ".aw" / "state" / "suite-baselines" / "x1y2z3-attempt1",
        )
        self.assertEqual(
            runner_shared.state_root(repo), repo / ".aw" / "records" / "runs"
        )
        self.assertEqual(
            attention._resolve_runs_repo_root(repo).resolve(), repo.resolve()
        )


if __name__ == "__main__":
    unittest.main()
