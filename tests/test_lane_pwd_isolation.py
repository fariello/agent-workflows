"""Behavioral outcome tests for vl3pvt: isolated lane turns must not inherit driver PWD/OLDPWD.

OpenCode v2 dropped `run --dir` and resolves its workspace from `$PWD` before falling back to
`getcwd()`. Python's `subprocess.Popen(..., cwd=lane_dir, env=child_env)` updates the OS cwd
but leaves `child_env["PWD"]` pointing at the driver's main checkout unless stripped. These tests
launch real stub executables through `run_opencode`, `observe_opencode_policy`, `run_agy_turn`,
and `runner_shared.run_checked`, and verify what the child processes actually observe.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from agent_workflows import agy_runipd, oc_runipd, runner_shared
from tests import support


def _init_git_repo(repo: Path) -> None:
    repo.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.invalid"],
        cwd=repo,
        check=True,
    )
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
    (repo / "README").write_text("test\n", encoding="utf-8")
    subprocess.run(["git", "add", "README"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "initial"], cwd=repo, check=True)


def _write_recording_stub(script_path: Path, record_path: Path, *, mode: str) -> Path:
    """Create an executable script that records its observed PWD, OLDPWD, and os.getcwd()."""
    if mode == "opencode":
        body = f"""#!{sys.executable}
import json, os, sys
args = sys.argv[1:]
if args == ["--version"]:
    print("opencode v2.3.2")
    raise SystemExit(0)
if args == ["debug", "config"]:
    out_path = {str(record_path)!r} + ".probe"
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump({{"pwd": os.environ.get("PWD"), "oldpwd": os.environ.get("OLDPWD"), "cwd": os.getcwd()}}, fh)
    print(json.dumps({{"permission": {{"external_directory": "deny", "question": "deny"}}}}))
    raise SystemExit(0)
with open({str(record_path)!r}, "w", encoding="utf-8") as fh:
    json.dump({{"pwd": os.environ.get("PWD"), "oldpwd": os.environ.get("OLDPWD"), "cwd": os.getcwd(), "argv": args}}, fh)
print(json.dumps({{"type": "step_finish", "sessionID": "ses_test_pwd", "part": {{"type": "step-finish"}}}}))
"""
    elif mode == "agy":
        body = f"""#!{sys.executable}
import json, os, sys
with open({str(record_path)!r}, "w", encoding="utf-8") as fh:
    json.dump({{"pwd": os.environ.get("PWD"), "oldpwd": os.environ.get("OLDPWD"), "cwd": os.getcwd()}}, fh)
print(json.dumps({{"event": "result", "result": {{"status": "SUCCESS", "conversation_id": "conv_pwd", "response": "ok"}}}}))
"""
    else:
        raise ValueError(mode)
    return support.make_fake_executable(script_path, body)


class LanePwdIsolationTests(unittest.TestCase):
    def test_run_opencode_strips_inherited_pwd_and_oldpwd_in_lane(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "main-checkout"
            lane = root / "lane-worktree"
            run_dir = root / "run"
            _init_git_repo(repo)
            _init_git_repo(lane)
            run_dir.mkdir()

            plan_path = lane / "plan.ipd.md"
            plan_path.write_text("# Plan\n", encoding="utf-8")
            prompt_path = run_dir / "prompt.md"
            prompt_path.write_text("do work\n", encoding="utf-8")

            record_path = root / "oc-observed.json"
            stub = _write_recording_stub(
                root / "fake-opencode", record_path, mode="opencode"
            )

            state = {
                "run_id": "run-test-vl3pvt-oc",
                "repo": str(repo),
                "options": {"opencode": str(stub), "output_mode": "quiet"},
            }
            item = {
                "id6": "tst001",
                "setid": "tstset",
                "position": 1,
                "action": "execute",
            }

            with mock.patch.dict(
                os.environ,
                {"PWD": str(repo), "OLDPWD": str(repo)},
                clear=False,
            ):
                rc, sid, _log, _argv = oc_runipd.run_opencode(
                    state,
                    run_dir,
                    item,
                    plan_path,
                    prompt_path,
                    attempt_no=1,
                    work_dir=str(lane),
                )

            self.assertEqual(rc, 0)
            self.assertEqual(sid, "ses_test_pwd")

            observed = json.loads(record_path.read_text(encoding="utf-8"))
            self.assertIsNone(observed["pwd"])
            self.assertIsNone(observed["oldpwd"])
            self.assertEqual(os.path.realpath(observed["cwd"]), os.path.realpath(lane))
            self.assertNotIn("--dir", observed["argv"])

            probe_observed = json.loads(
                Path(str(record_path) + ".probe").read_text(encoding="utf-8")
            )
            self.assertIsNone(probe_observed["pwd"])
            self.assertIsNone(probe_observed["oldpwd"])
            self.assertEqual(
                os.path.realpath(probe_observed["cwd"]), os.path.realpath(lane)
            )

    def test_run_agy_turn_strips_inherited_pwd_and_oldpwd_in_lane(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "main-checkout"
            lane = root / "lane-worktree"
            run_dir = root / "run"
            _init_git_repo(repo)
            _init_git_repo(lane)
            run_dir.mkdir()

            prompt_path = run_dir / "prompt.md"
            prompt_path.write_text("do work\n", encoding="utf-8")

            record_path = root / "agy-observed.json"
            stub = _write_recording_stub(root / "fake-agy", record_path, mode="agy")

            state = {
                "run_id": "run-test-vl3pvt-agy",
                "repo": str(repo),
                "options": {"agy_executable": str(stub), "output_mode": "quiet"},
            }
            item = {
                "id6": "tst002",
                "setid": "tstset",
                "position": 1,
                "action": "execute",
            }

            with mock.patch.dict(
                os.environ,
                {"PWD": str(repo), "OLDPWD": str(repo)},
                clear=False,
            ):
                rc, sid, _log, _argv = agy_runipd.run_agy_turn(
                    state,
                    run_dir,
                    item,
                    prompt_path,
                    attempt_no=1,
                    session_id=None,
                    use_continue=False,
                    work_dir=str(lane),
                )

            self.assertEqual(rc, 0)
            self.assertEqual(sid, "conv_pwd")

            observed = json.loads(record_path.read_text(encoding="utf-8"))
            self.assertIsNone(observed["pwd"])
            self.assertIsNone(observed["oldpwd"])
            self.assertEqual(os.path.realpath(observed["cwd"]), os.path.realpath(lane))

    def test_run_checked_strips_pwd_and_oldpwd_when_cwd_given(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            caller_dir = root / "caller"
            target_dir = root / "target"
            caller_dir.mkdir()
            target_dir.mkdir()

            with mock.patch.dict(
                os.environ,
                {"PWD": str(caller_dir), "OLDPWD": str(caller_dir)},
                clear=False,
            ):
                out = runner_shared.run_checked(
                    [
                        sys.executable,
                        "-c",
                        (
                            "import json, os; "
                            "print(json.dumps({"
                            "'pwd': os.environ.get('PWD'), "
                            "'oldpwd': os.environ.get('OLDPWD'), "
                            "'cwd': os.getcwd()}))"
                        ),
                    ],
                    cwd=target_dir,
                    env_builder=runner_shared.pinned_child_env,
                )

            observed = json.loads(out)
            self.assertIsNone(observed["pwd"])
            self.assertIsNone(observed["oldpwd"])
            self.assertEqual(
                os.path.realpath(observed["cwd"]), os.path.realpath(target_dir)
            )


if __name__ == "__main__":
    unittest.main()
