"""Tests for AW_RUN_ID and AW_ITEM_ID6 environment variables in aw commit (IPD a6xbso).

Covers:
(1) Scratch-repo end to end with valid AW_RUN_ID and AW_ITEM_ID6.
(2) Byte-identity without env vars.
(3) Malformed env values dropped with a warning on stderr.
(4) Namespace precedence over env vars.
(5) oc_runipd child-env export and overwrite-or-pop.
(6) agy_runipd child-env export and overwrite-or-pop.
(7) conftest.py import-time scrub of both env vars.
(8) Round-trip agreement between runner export and work_cmd reader (E-08).
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest import mock


from agent_workflows import agy_runipd
from agent_workflows import git_commit_helper as _gch
from agent_workflows import oc_runipd
from agent_workflows import runner_shared
from agent_workflows import work_cmd

_REPO_ROOT = Path(__file__).resolve().parent.parent


def _init_repo(path: Path) -> Path:
    subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=path,
        check=True,
        capture_output=True,
    )
    f = path / "f"
    f.write_text("initial\n", encoding="utf-8")
    subprocess.run(["git", "add", "f"], cwd=path, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "init"], cwd=path, check=True, capture_output=True
    )
    return f


def _raw_commit_body(repo: Path) -> str:
    res = subprocess.run(
        ["git", "cat-file", "commit", "HEAD"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    return res.stdout.split("\n\n", 1)[1]


def test_scratch_repo_end_to_end_stamps_trailers():
    """Case 1: SCRATCH-REPO END TO END with valid AW_RUN_ID and AW_ITEM_ID6."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo = Path(tmpdir)
        f = _init_repo(repo)
        f.write_text("modified\n", encoding="utf-8")

        env = os.environ.copy()
        env[_gch.RUN_ID_ENV] = "run-20260926T010203Z-4242"
        env[_gch.ITEM_ID6_ENV] = "abc123"
        env["PYTHONPATH"] = str(_REPO_ROOT)

        proc = subprocess.run(
            [
                sys.executable,
                "-m",
                "agent_workflows",
                "commit",
                "--no-plan",
                "-m",
                "x",
                "--",
                "f",
            ],
            cwd=repo,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        assert proc.returncode == 0, f"stdout: {proc.stdout}\nstderr: {proc.stderr}"

        log_run = subprocess.run(
            ["git", "log", "-1", "--format=%(trailers:key=AW-Run,valueonly)"],
            cwd=repo,
            check=True,
            capture_output=True,
            text=True,
        )
        assert log_run.stdout.strip() == "run-20260926T010203Z-4242"

        log_item = subprocess.run(
            ["git", "log", "-1", "--format=%(trailers:key=AW-Item,valueonly)"],
            cwd=repo,
            check=True,
            capture_output=True,
            text=True,
        )
        assert log_item.stdout.strip() == "abc123"


def test_byte_identity_without_env_vars():
    """Case 2: BYTE-IDENTITY WITHOUT ENV: stored commit body is exactly 'x\\n'."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo = Path(tmpdir)
        f = _init_repo(repo)
        f.write_text("modified\n", encoding="utf-8")

        env = os.environ.copy()
        env.pop(_gch.RUN_ID_ENV, None)
        env.pop(_gch.ITEM_ID6_ENV, None)
        env["PYTHONPATH"] = str(_REPO_ROOT)

        proc = subprocess.run(
            [
                sys.executable,
                "-m",
                "agent_workflows",
                "commit",
                "--no-plan",
                "-m",
                "x",
                "--",
                "f",
            ],
            cwd=repo,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        assert proc.returncode == 0, f"stdout: {proc.stdout}\nstderr: {proc.stderr}"
        assert _raw_commit_body(repo) == "x\n"


def test_malformed_values_dropped_with_warning():
    """Case 3: MALFORMED VALUES: dropped with one stderr line warning, valid companion kept."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo = Path(tmpdir)
        f = _init_repo(repo)

        # 3a: malformed run id, valid id6
        f.write_text("mod 1\n", encoding="utf-8")
        env1 = os.environ.copy()
        env1[_gch.RUN_ID_ENV] = "../evil"
        env1[_gch.ITEM_ID6_ENV] = "abc123"
        env1["PYTHONPATH"] = str(_REPO_ROOT)

        proc1 = subprocess.run(
            [
                sys.executable,
                "-m",
                "agent_workflows",
                "commit",
                "--no-plan",
                "-m",
                "x",
                "--",
                "f",
            ],
            cwd=repo,
            env=env1,
            capture_output=True,
            text=True,
            check=False,
        )
        assert proc1.returncode == 0
        assert _gch.RUN_ID_ENV in proc1.stderr
        assert "warning - ignoring malformed" in proc1.stderr

        log1_run = subprocess.run(
            ["git", "log", "-1", "--format=%(trailers:key=AW-Run,valueonly)"],
            cwd=repo,
            check=True,
            capture_output=True,
            text=True,
        )
        assert log1_run.stdout.strip() == ""

        log1_item = subprocess.run(
            ["git", "log", "-1", "--format=%(trailers:key=AW-Item,valueonly)"],
            cwd=repo,
            check=True,
            capture_output=True,
            text=True,
        )
        assert log1_item.stdout.strip() == "abc123"

        # 3b: malformed id6, valid run id
        f.write_text("mod 2\n", encoding="utf-8")
        env2 = os.environ.copy()
        env2[_gch.RUN_ID_ENV] = "run-20260926T010203Z-4242"
        env2[_gch.ITEM_ID6_ENV] = "ABC!23"
        env2["PYTHONPATH"] = str(_REPO_ROOT)

        proc2 = subprocess.run(
            [
                sys.executable,
                "-m",
                "agent_workflows",
                "commit",
                "--no-plan",
                "-m",
                "x",
                "--",
                "f",
            ],
            cwd=repo,
            env=env2,
            capture_output=True,
            text=True,
            check=False,
        )
        assert proc2.returncode == 0
        assert _gch.ITEM_ID6_ENV in proc2.stderr
        assert "warning - ignoring malformed" in proc2.stderr

        log2_run = subprocess.run(
            ["git", "log", "-1", "--format=%(trailers:key=AW-Run,valueonly)"],
            cwd=repo,
            check=True,
            capture_output=True,
            text=True,
        )
        assert log2_run.stdout.strip() == "run-20260926T010203Z-4242"

        log2_item = subprocess.run(
            ["git", "log", "-1", "--format=%(trailers:key=AW-Item,valueonly)"],
            cwd=repo,
            check=True,
            capture_output=True,
            text=True,
        )
        assert log2_item.stdout.strip() == ""


def test_namespace_precedence_over_env_vars():
    """Case 4: NAMESPACE PRECEDENCE: explicit namespace attrs override ambient env vars."""
    with mock.patch.dict(
        os.environ,
        {
            _gch.RUN_ID_ENV: "run-20260926T010203Z-4242",
            _gch.ITEM_ID6_ENV: "abc123",
        },
    ):
        ns = argparse.Namespace(run_id="run-20260101T000000Z-1", item_id6="zzz999")
        trailers = work_cmd._trailers_from_args(ns)
        assert trailers == [
            "AW-Run: run-20260101T000000Z-1",
            "AW-Item: zzz999",
        ]


def test_oc_stub_agent_env_dump():
    """Case 5: OC STUB-AGENT ENV DUMP: run_opencode exports AW_RUN_ID and AW_ITEM_ID6 verbatim.

    Note (F-8): The reused harness's run_id is 'run-test', which the writer exports verbatim
    and the reader later rejects. This test proves that the writer exports the live run's state,
    not that 'run-test' is usable end to end. End-to-end usability is proven by E-08.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        run_dir = root / ".aw" / "records" / "runs" / "run-test"
        (run_dir / "sessions").mkdir(parents=True, exist_ok=True)
        prompt_path = root / "prompt.md"
        prompt_path.write_text("do something", encoding="utf-8")
        plan_path = root / "plan.ipd.md"
        plan_path.write_text("plan", encoding="utf-8")

        state = {
            "run_id": "run-test",
            "options": {
                "opencode": "opencode",
                "agy_executable": "agy",
                "stall_timeout": 10.0,
                "timeout": 10.0,
            },
            "repo": str(root),
            "queue": [],
        }
        item = {"position": 1, "id6": "abc123", "setid": "demo"}

        # Assertion 5a: state has run_id and item has id6 -> both exported to child env
        with mock.patch(
            "agent_workflows.oc_runipd.observe_opencode_policy", return_value="observed"
        ):
            with mock.patch("agent_workflows.lane_containment.record_host_posture"):
                with mock.patch("subprocess.Popen") as mock_popen:
                    mock_popen.return_value.poll.return_value = 0
                    mock_popen.return_value.returncode = 0
                    mock_popen.return_value.stdout = io_empty = mock.MagicMock()
                    mock_popen.return_value.stderr = mock.MagicMock()
                    io_empty.readline.return_value = ""

                    oc_runipd.run_opencode(
                        state=state,
                        run_dir=run_dir,
                        item=item,
                        plan_path=plan_path,
                        prompt_path=prompt_path,
                        attempt_no=1,
                        work_dir=str(root / "worktree"),
                    )

                    assert mock_popen.called
                    child_env = mock_popen.call_args[1].get("env", {})
                    assert child_env.get(_gch.RUN_ID_ENV) == "run-test"
                    assert child_env.get(_gch.ITEM_ID6_ENV) == "abc123"

        # Assertion 5b: state WITHOUT run_id pops inherited AW_RUN_ID
        state_no_run = {
            "run_id": "",
            "options": {
                "opencode": "opencode",
                "agy_executable": "agy",
                "stall_timeout": 10.0,
                "timeout": 10.0,
            },
            "repo": str(root),
            "queue": [],
        }
        with mock.patch.dict(os.environ, {_gch.RUN_ID_ENV: "run-19990101T000000Z-1"}):
            with mock.patch(
                "agent_workflows.oc_runipd.observe_opencode_policy",
                return_value="observed",
            ):
                with mock.patch("agent_workflows.lane_containment.record_host_posture"):
                    with mock.patch("subprocess.Popen") as mock_popen:
                        mock_popen.return_value.poll.return_value = 0
                        mock_popen.return_value.returncode = 0
                        mock_popen.return_value.stdout = io_empty = mock.MagicMock()
                        mock_popen.return_value.stderr = mock.MagicMock()
                        io_empty.readline.return_value = ""

                        oc_runipd.run_opencode(
                            state=state_no_run,
                            run_dir=run_dir,
                            item=item,
                            plan_path=plan_path,
                            prompt_path=prompt_path,
                            attempt_no=1,
                            work_dir=str(root / "worktree"),
                        )

                        assert mock_popen.called
                        child_env = mock_popen.call_args[1].get("env", {})
                        assert _gch.RUN_ID_ENV not in child_env


def test_agy_stub_agent_env_dump():
    """Case 6: AGY STUB-AGENT ENV DUMP: run_agy_turn exports AW_RUN_ID and AW_ITEM_ID6 verbatim."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        run_dir = root / ".aw" / "records" / "runs" / "run-test"
        (run_dir / "sessions").mkdir(parents=True, exist_ok=True)
        prompt_path = root / "prompt.md"
        prompt_path.write_text("do something", encoding="utf-8")

        state = {
            "run_id": "run-test",
            "options": {
                "opencode": "opencode",
                "agy_executable": "agy",
                "stall_timeout": 10.0,
                "timeout": 10.0,
            },
            "repo": str(root),
            "queue": [],
        }
        item = {"position": 1, "id6": "abc123", "setid": "demo"}

        # Assertion 6a: state has run_id and item has id6 -> both exported to child env
        with mock.patch("agent_workflows.lane_containment.record_host_posture"):
            with mock.patch("subprocess.Popen") as mock_popen_agy:
                mock_popen_agy.return_value.poll.return_value = 0
                mock_popen_agy.return_value.returncode = 0
                mock_popen_agy.return_value.stdout = mock.MagicMock()
                mock_popen_agy.return_value.stderr = mock.MagicMock()

                agy_runipd.run_agy_turn(
                    state=state,
                    run_dir=run_dir,
                    item=item,
                    prompt_path=prompt_path,
                    attempt_no=1,
                    session_id=None,
                    use_continue=False,
                    work_dir=str(root / "worktree"),
                )

                assert mock_popen_agy.called
                child_env = mock_popen_agy.call_args[1].get("env", {})
                assert child_env.get(_gch.RUN_ID_ENV) == "run-test"
                assert child_env.get(_gch.ITEM_ID6_ENV) == "abc123"

        # Assertion 6b: state WITHOUT run_id pops inherited AW_RUN_ID
        state_no_run = {
            "options": {
                "opencode": "opencode",
                "agy_executable": "agy",
                "stall_timeout": 10.0,
                "timeout": 10.0,
            },
            "repo": str(root),
            "queue": [],
        }
        with mock.patch.dict(os.environ, {_gch.RUN_ID_ENV: "run-19990101T000000Z-1"}):
            with mock.patch("agent_workflows.lane_containment.record_host_posture"):
                with mock.patch("subprocess.Popen") as mock_popen_agy:
                    mock_popen_agy.return_value.poll.return_value = 0
                    mock_popen_agy.return_value.returncode = 0
                    mock_popen_agy.return_value.stdout = mock.MagicMock()
                    mock_popen_agy.return_value.stderr = mock.MagicMock()

                    agy_runipd.run_agy_turn(
                        state=state_no_run,
                        run_dir=run_dir,
                        item=item,
                        prompt_path=prompt_path,
                        attempt_no=1,
                        session_id=None,
                        use_continue=False,
                        work_dir=str(root / "worktree"),
                    )

                    assert mock_popen_agy.called
                    child_env = mock_popen_agy.call_args[1].get("env", {})
                    assert _gch.RUN_ID_ENV not in child_env


def test_conftest_scrubs_run_and_item_env_vars():
    """Case 7: CONFTEST SCRUB: os.environ holds neither AW_RUN_ID nor AW_ITEM_ID6 at session start."""
    assert _gch.RUN_ID_ENV not in os.environ
    assert _gch.ITEM_ID6_ENV not in os.environ


def test_round_trip_writer_export_to_reader_trailers():
    """Case 8 (E-08): Writer-exported AW_RUN_ID round-trips into work_cmd reader trailers.

    Tested for both plain new_run_id() shape and oc_runipd -N suffixed shape.
    The run id asserted comes directly from the captured child env, not re-typed.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        run_dir = root / ".aw" / "records" / "runs" / "run-test"
        (run_dir / "sessions").mkdir(parents=True, exist_ok=True)
        prompt_path = root / "prompt.md"
        prompt_path.write_text("do something", encoding="utf-8")
        plan_path = root / "plan.ipd.md"
        plan_path.write_text("plan", encoding="utf-8")
        item = {"position": 1, "id6": "abc123", "setid": "demo"}

        # 8a: plain new_run_id shape
        plain_id = runner_shared.new_run_id()
        state_plain = {
            "run_id": plain_id,
            "options": {"opencode": "opencode", "agy_executable": "agy"},
            "repo": str(root),
            "queue": [],
        }

        with mock.patch(
            "agent_workflows.oc_runipd.observe_opencode_policy", return_value="observed"
        ):
            with mock.patch("agent_workflows.lane_containment.record_host_posture"):
                with mock.patch("subprocess.Popen") as mock_popen:
                    mock_popen.return_value.poll.return_value = 0
                    mock_popen.return_value.returncode = 0
                    mock_popen.return_value.stdout = io_empty = mock.MagicMock()
                    mock_popen.return_value.stderr = mock.MagicMock()
                    io_empty.readline.return_value = ""

                    oc_runipd.run_opencode(
                        state=state_plain,
                        run_dir=run_dir,
                        item=item,
                        plan_path=plan_path,
                        prompt_path=prompt_path,
                        attempt_no=1,
                        work_dir=str(root / "worktree"),
                    )

                    child_env = mock_popen.call_args[1].get("env", {})
                    captured_run_id = child_env.get(_gch.RUN_ID_ENV)
                    captured_item_id = child_env.get(_gch.ITEM_ID6_ENV)

        assert captured_run_id == plain_id
        assert captured_item_id == "abc123"

        # Now pass the captured values to work_cmd reader via environment
        with mock.patch.dict(
            os.environ,
            {_gch.RUN_ID_ENV: captured_run_id, _gch.ITEM_ID6_ENV: captured_item_id},
        ):
            trailers_plain = work_cmd._trailers_from_args(argparse.Namespace())
            assert f"AW-Run: {captured_run_id}" in trailers_plain
            assert f"AW-Item: {captured_item_id}" in trailers_plain

        # 8b: -N collision suffix shape
        suffixed_id = f"{plain_id}-1"
        state_suffixed = {
            "run_id": suffixed_id,
            "options": {"opencode": "opencode", "agy_executable": "agy"},
            "repo": str(root),
            "queue": [],
        }

        with mock.patch(
            "agent_workflows.oc_runipd.observe_opencode_policy", return_value="observed"
        ):
            with mock.patch("agent_workflows.lane_containment.record_host_posture"):
                with mock.patch("subprocess.Popen") as mock_popen:
                    mock_popen.return_value.poll.return_value = 0
                    mock_popen.return_value.returncode = 0
                    mock_popen.return_value.stdout = io_empty = mock.MagicMock()
                    mock_popen.return_value.stderr = mock.MagicMock()
                    io_empty.readline.return_value = ""

                    oc_runipd.run_opencode(
                        state=state_suffixed,
                        run_dir=run_dir,
                        item=item,
                        plan_path=plan_path,
                        prompt_path=prompt_path,
                        attempt_no=1,
                        work_dir=str(root / "worktree"),
                    )

                    child_env = mock_popen.call_args[1].get("env", {})
                    captured_suffixed_id = child_env.get(_gch.RUN_ID_ENV)

        assert captured_suffixed_id == suffixed_id

        with mock.patch.dict(
            os.environ,
            {
                _gch.RUN_ID_ENV: captured_suffixed_id,
                _gch.ITEM_ID6_ENV: captured_item_id,
            },
        ):
            trailers_suffixed = work_cmd._trailers_from_args(argparse.Namespace())
            assert f"AW-Run: {captured_suffixed_id}" in trailers_suffixed
            assert f"AW-Item: {captured_item_id}" in trailers_suffixed
