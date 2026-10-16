"""Behavioral tests for operator user-config containment (IPD 9y27t2).

P16: behavioral only (drive code, assert outputs and side effects; no source reading).
Cells:
(a) AW_CONFIG_DIR precedence
(b) Seed fidelity
(c) The incident end to end per host (oc_runipd and agy_runipd)
(c2) Nonzero exit and Popen raise still reconcile and clean up sandbox
(d) Overwrite-or-pop child env
(e) report_discarded_user_config output
(f) Conftest scrub of AW_CONFIG_DIR
"""

from __future__ import annotations

import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest import mock

import pytest

from agent_workflows import agy_runipd
from agent_workflows import config
from agent_workflows import oc_runipd
from agent_workflows import runner_shared

_REPO_ROOT = Path(__file__).resolve().parent.parent


def test_aw_config_dir_precedence():
    """Cell (a): AW_CONFIG_DIR precedence over XDG_CONFIG_HOME and fallback guards."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        x = tmp / "xdg"
        d = tmp / "sandbox"
        h = tmp / "home"
        x.mkdir()
        d.mkdir()
        h.mkdir()

        env_base = {
            **os.environ,
            "AW_NO_REEXEC": "1",
            "PYTHONPATH": str(_REPO_ROOT),
        }

        # Case 1: XDG_CONFIG_HOME=<x> and AW_CONFIG_DIR=<d>
        env1 = {**env_base, "XDG_CONFIG_HOME": str(x), "AW_CONFIG_DIR": str(d)}
        proc1 = subprocess.run(
            [
                sys.executable,
                "-m",
                "agent_workflows",
                "config",
                "set",
                "color_depth",
                "16",
            ],
            env=env1,
            capture_output=True,
            text=True,
            check=False,
        )
        assert proc1.returncode == 0, f"stderr: {proc1.stderr}"
        assert (d / "config.json").is_file()
        assert not (x / "agent-workflows").exists()
        cfg_d = json.loads((d / "config.json").read_text(encoding="utf-8"))
        assert cfg_d.get("color_depth") == "16"

        # Case 2: AW_CONFIG_DIR unset -> falls back to <x>/agent-workflows
        env2 = {**env_base, "XDG_CONFIG_HOME": str(x)}
        env2.pop("AW_CONFIG_DIR", None)
        proc2 = subprocess.run(
            [
                sys.executable,
                "-m",
                "agent_workflows",
                "config",
                "set",
                "color_depth",
                "16",
            ],
            env=env2,
            capture_output=True,
            text=True,
            check=False,
        )
        assert proc2.returncode == 0, f"stderr: {proc2.stderr}"
        assert (x / "agent-workflows" / "config.json").is_file()
        cfg_x = json.loads(
            (x / "agent-workflows" / "config.json").read_text(encoding="utf-8")
        )
        assert cfg_x.get("color_depth") == "16"

        shutil.rmtree(x / "agent-workflows")

        # Case 3: relative AW_CONFIG_DIR -> ignored, falls back to <x>/agent-workflows
        env3 = {**env_base, "XDG_CONFIG_HOME": str(x), "AW_CONFIG_DIR": "relative-dir"}
        proc3 = subprocess.run(
            [
                sys.executable,
                "-m",
                "agent_workflows",
                "config",
                "set",
                "color_depth",
                "16",
            ],
            env=env3,
            cwd=str(tmp),
            capture_output=True,
            text=True,
            check=False,
        )
        assert proc3.returncode == 0, f"stderr: {proc3.stderr}"
        assert not (tmp / "relative-dir").exists()
        assert (x / "agent-workflows" / "config.json").is_file()

        shutil.rmtree(x / "agent-workflows")

        # Case 4: AW_CONFIG_DIR equal to HOME -> ignored, falls back to <x>/agent-workflows
        env4 = {
            **env_base,
            "HOME": str(h),
            "XDG_CONFIG_HOME": str(x),
            "AW_CONFIG_DIR": str(h),
        }
        proc4 = subprocess.run(
            [
                sys.executable,
                "-m",
                "agent_workflows",
                "config",
                "set",
                "color_depth",
                "16",
            ],
            env=env4,
            capture_output=True,
            text=True,
            check=False,
        )
        assert proc4.returncode == 0, f"stderr: {proc4.stderr}"
        assert not (h / "config.json").exists()
        assert (x / "agent-workflows" / "config.json").is_file()


def test_seed_fidelity():
    """Cell (b): prepare_agent_user_config copies files faithfully and reads operator settings."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        source = tmp / "operator_cfg"
        source.mkdir()
        run_dir = tmp / "run"
        run_dir.mkdir()

        cfg_data = config.default_config()
        cfg_data["color_depth"] = "256"
        (source / "config.json").write_text(json.dumps(cfg_data), encoding="utf-8")
        profiles_data = {"version": 1, "profiles": {"fast": {"model": "claude-haiku"}}}
        (source / "runner-profiles.json").write_text(
            json.dumps(profiles_data), encoding="utf-8"
        )

        item = {"position": 1, "id6": "9y27t2"}
        handle = runner_shared.prepare_agent_user_config(
            run_dir, item, attempt_no=1, suffix="", source_dir=source
        )
        assert handle is not None
        assert handle.path.is_dir()

        # Byte-identical copies
        assert (handle.path / "config.json").read_bytes() == (
            source / "config.json"
        ).read_bytes()
        assert (handle.path / "runner-profiles.json").read_bytes() == (
            source / "runner-profiles.json"
        ).read_bytes()

        # Reading color_depth using the exported env returns the operator's value
        env = {
            **os.environ,
            "AW_NO_REEXEC": "1",
            "PYTHONPATH": str(_REPO_ROOT),
            config.CONFIG_DIR_ENV: str(handle.path),
        }
        proc = subprocess.run(
            [sys.executable, "-m", "agent_workflows", "config", "get", "color_depth"],
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        assert proc.returncode == 0, f"stderr: {proc.stderr}"
        assert proc.stdout.strip() == "256"

        runner_shared.reconcile_agent_user_config(handle, run_dir, item)


def test_incident_end_to_end_per_host(capsys):
    """Cell (c): The incident end to end per host (oc_runipd and agy_runipd).

    Agent writes color_depth none; operator config is untouched; event is recorded
    with keys == ['color_depth'] and no value none; stderr carries DISCARDED line;
    sandbox is deleted; verify turn records separately.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        xdg = tmp / "xdg"
        xdg_aw = xdg / "agent-workflows"
        xdg_aw.mkdir(parents=True)
        real_cfg = xdg_aw / "config.json"
        initial_cfg = config.default_config()
        initial_cfg["color_depth"] = "16"
        real_cfg.write_text(json.dumps(initial_cfg), encoding="utf-8")
        orig_bytes = real_cfg.read_bytes()

        # Host script that writes color_depth none
        from tests import support

        script = support.make_fake_executable(
            tmp / "fake_agent",
            f"""#!/usr/bin/env python3
import os, subprocess, sys
env = dict(os.environ)
env["AW_NO_REEXEC"] = "1"
subprocess.run([{sys.executable!r}, "-m", "agent_workflows", "config", "set", "color_depth", "none"], env=env, stdout=subprocess.DEVNULL, check=True)
sys.exit(0)
""",
        )

        run_dir = tmp / "run"
        (run_dir / "sessions").mkdir(parents=True)
        (run_dir / "prompts").mkdir(parents=True)
        plan_path = tmp / "plan.ipd.md"
        plan_path.write_text("# Plan\n", encoding="utf-8")
        prompt_path = tmp / "prompt.md"
        prompt_path.write_text("prompt\n", encoding="utf-8")

        state = {
            "run_id": "run-test-incident",
            "repo": str(tmp),
            "options": {
                "opencode": str(script),
                "agy_executable": str(script),
                "stall_timeout": 10.0,
                "timeout": 10.0,
                "output_mode": "raw",
            },
            "queue": [],
        }
        item = {"position": 1, "id6": "9y27t2", "setid": "btw02e"}

        with mock.patch.dict(os.environ, {"XDG_CONFIG_HOME": str(xdg)}):
            # 1. Drive oc_runipd.run_opencode
            rc_oc, _, _, _ = oc_runipd.run_opencode(
                state=state,
                run_dir=run_dir,
                item=item,
                plan_path=plan_path,
                prompt_path=prompt_path,
                attempt_no=1,
            )
            assert rc_oc == 0
            assert real_cfg.read_bytes() == orig_bytes
            captured = capsys.readouterr()
            assert "DISCARDED" in captured.err
            assert (
                "IPD 9y27t2: agent changed user config config.json (color_depth)"
                in captured.err
            )
            assert not (run_dir / "agent-user-config").exists() or not any(
                (run_dir / "agent-user-config").iterdir()
            )

            # Read events.jsonl
            events_path = run_dir / "events.jsonl"
            assert events_path.is_file()
            lines = [
                json.loads(line)
                for line in events_path.read_text().splitlines()
                if line.strip()
            ]
            discard_lines = [
                ev for ev in lines if ev.get("event") == "agent-user-config-discarded"
            ]
            assert len(discard_lines) == 1
            ev1 = discard_lines[0]
            assert ev1["event"] == "agent-user-config-discarded"
            assert ev1["id6"] == "9y27t2"
            assert ev1["file"] == "config.json"
            assert ev1["keys"] == ["color_depth"]
            assert "none" not in json.dumps(ev1)

            # 2. Drive agy_runipd.run_agy_turn
            rc_agy, _, _, _ = agy_runipd.run_agy_turn(
                state=state,
                run_dir=run_dir,
                item=item,
                prompt_path=prompt_path,
                attempt_no=1,
                session_id=None,
                use_continue=False,
            )
            assert rc_agy == 0
            assert real_cfg.read_bytes() == orig_bytes
            captured_agy = capsys.readouterr()
            assert "DISCARDED" in captured_agy.err
            assert (
                "IPD 9y27t2: agent changed user config config.json (color_depth)"
                in captured_agy.err
            )
            assert not (run_dir / "agent-user-config").exists() or not any(
                (run_dir / "agent-user-config").iterdir()
            )

            # Verify a second turn of same attempt with log_suffix="verify"
            rc_verify, _, _, _ = oc_runipd.run_opencode(
                state=state,
                run_dir=run_dir,
                item=item,
                plan_path=plan_path,
                prompt_path=prompt_path,
                attempt_no=1,
                log_suffix="verify",
            )
            assert rc_verify == 0
            assert real_cfg.read_bytes() == orig_bytes

            lines_after = [
                json.loads(line)
                for line in events_path.read_text().splitlines()
                if line.strip()
            ]
            discard_lines_after = [
                ev
                for ev in lines_after
                if ev.get("event") == "agent-user-config-discarded"
            ]
            assert (
                len(discard_lines_after) == 3
            )  # oc attempt 1, agy attempt 1, oc attempt 1 verify
            assert all(
                ev["event"] == "agent-user-config-discarded"
                for ev in discard_lines_after
            )


def test_turn_failure_and_popen_raise_still_reconciles():
    """Cell (c2): Nonzero exit and Popen raise still reconcile and clean up sandbox."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        xdg = tmp / "xdg"
        xdg_aw = xdg / "agent-workflows"
        xdg_aw.mkdir(parents=True)
        real_cfg = xdg_aw / "config.json"
        initial_cfg = config.default_config()
        real_cfg.write_text(json.dumps(initial_cfg), encoding="utf-8")
        orig_bytes = real_cfg.read_bytes()

        # Failing script
        from tests import support

        fail_script = support.make_fake_executable(
            tmp / "fail_agent",
            f"""#!/usr/bin/env python3
import os, subprocess, sys
env = dict(os.environ)
env["AW_NO_REEXEC"] = "1"
subprocess.run([{sys.executable!r}, "-m", "agent_workflows", "config", "set", "color_depth", "none"], env=env, stdout=subprocess.DEVNULL, check=True)
sys.exit(42)
""",
        )

        run_dir = tmp / "run"
        (run_dir / "sessions").mkdir(parents=True)
        (run_dir / "prompts").mkdir(parents=True)
        plan_path = tmp / "plan.ipd.md"
        plan_path.write_text("# Plan\n", encoding="utf-8")
        prompt_path = tmp / "prompt.md"
        prompt_path.write_text("prompt\n", encoding="utf-8")

        state = {
            "run_id": "run-test-fail",
            "repo": str(tmp),
            "options": {
                "opencode": str(fail_script),
                "agy_executable": str(fail_script),
                "stall_timeout": 10.0,
                "timeout": 10.0,
                "output_mode": "raw",
            },
            "queue": [],
        }
        item = {"position": 1, "id6": "9y27t2", "setid": "btw02e"}

        with mock.patch.dict(os.environ, {"XDG_CONFIG_HOME": str(xdg)}):
            # Nonzero exit in oc_runipd
            rc_oc, _, _, _ = oc_runipd.run_opencode(
                state=state,
                run_dir=run_dir,
                item=item,
                plan_path=plan_path,
                prompt_path=prompt_path,
                attempt_no=1,
            )
            assert rc_oc == 42
            assert real_cfg.read_bytes() == orig_bytes
            assert not (run_dir / "agent-user-config").exists() or not any(
                (run_dir / "agent-user-config").iterdir()
            )

            # Popen raise in oc_runipd
            with mock.patch("subprocess.Popen", side_effect=OSError("launch failed")):
                with pytest.raises(OSError, match="launch failed"):
                    oc_runipd.run_opencode(
                        state=state,
                        run_dir=run_dir,
                        item=item,
                        plan_path=plan_path,
                        prompt_path=prompt_path,
                        attempt_no=2,
                    )
            assert real_cfg.read_bytes() == orig_bytes
            assert not (run_dir / "agent-user-config").exists() or not any(
                (run_dir / "agent-user-config").iterdir()
            )


def test_overwrite_or_pop_child_env():
    """Cell (d): Overwrite-or-pop: Outer AW_CONFIG_DIR is never inherited."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        run_dir = root / ".aw" / "records" / "runs" / "run-test"
        (run_dir / "sessions").mkdir(parents=True, exist_ok=True)
        (run_dir / "prompts").mkdir(parents=True, exist_ok=True)
        plan_path = root / "plan.ipd.md"
        plan_path.write_text("# Plan\n", encoding="utf-8")
        prompt_path = root / "prompt.md"
        prompt_path.write_text("do something\n", encoding="utf-8")

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
        item = {"position": 1, "id6": "9y27t2", "setid": "demo"}

        # Sub-case 1: Seeding succeeds -> child env receives new per-turn path, never /outer
        with mock.patch.dict(os.environ, {config.CONFIG_DIR_ENV: "/outer"}):
            with mock.patch("subprocess.Popen") as mock_popen:
                mock_popen.return_value.poll.return_value = 0
                mock_popen.return_value.returncode = 0
                mock_popen.return_value.stdout = io.StringIO("")
                mock_popen.return_value.wait.return_value = 0

                oc_runipd.run_opencode(
                    state=state,
                    run_dir=run_dir,
                    item=item,
                    plan_path=plan_path,
                    prompt_path=prompt_path,
                    attempt_no=1,
                )
                assert mock_popen.called
                child_env = mock_popen.call_args[1].get("env", {})
                assert config.CONFIG_DIR_ENV in child_env
                assert child_env[config.CONFIG_DIR_ENV] != "/outer"
                assert "01-9y27t2-attempt-1" in child_env[config.CONFIG_DIR_ENV]

        # Sub-case 2: Seeding forced to fail -> child env has NO AW_CONFIG_DIR
        with mock.patch.dict(os.environ, {config.CONFIG_DIR_ENV: "/outer"}):
            with mock.patch(
                "agent_workflows.runner_shared.prepare_agent_user_config",
                return_value=None,
            ):
                with mock.patch("subprocess.Popen") as mock_popen:
                    mock_popen.return_value.poll.return_value = 0
                    mock_popen.return_value.returncode = 0
                    mock_popen.return_value.stdout = io.StringIO("")
                    mock_popen.return_value.wait.return_value = 0

                    oc_runipd.run_opencode(
                        state=state,
                        run_dir=run_dir,
                        item=item,
                        plan_path=plan_path,
                        prompt_path=prompt_path,
                        attempt_no=1,
                    )
                    assert mock_popen.called
                    child_env = mock_popen.call_args[1].get("env", {})
                    assert config.CONFIG_DIR_ENV not in child_env


def test_report_discarded_user_config_output():
    """Cell (e): report_discarded_user_config prints summary for events and nothing for clean."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)

        # 1. Run dir with one event
        run1 = tmp / "run1"
        run1.mkdir()
        runner_shared.append_jsonl(
            run1 / "events.jsonl",
            {
                "event": "agent-user-config-discarded",
                "id6": "9y27t2",
                "file": "config.json",
                "keys": ["color_depth"],
            },
        )
        out1 = io.StringIO()
        runner_shared.report_discarded_user_config(run1, stream=out1)
        assert (
            "Agent user-config changes discarded: 1 (9y27t2: config.json ['color_depth'])"
            in out1.getvalue()
        )

        # 2. Run dir without event
        run2 = tmp / "run2"
        run2.mkdir()
        out2 = io.StringIO()
        runner_shared.report_discarded_user_config(run2, stream=out2)
        assert out2.getvalue() == ""


def test_conftest_scrub():
    """Cell (f): AW_CONFIG_DIR is absent from os.environ inside a test."""
    assert config.CONFIG_DIR_ENV not in os.environ


def test_profiles_subdirectory_containment():
    """Cell (g) / E-05: profiles/ subdirectory seeding, byte-identical copy, modification reconciliation, and source preservation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        source = tmp / "operator_cfg"
        source.mkdir()
        profiles_dir = source / "profiles"
        profiles_dir.mkdir()
        run_dir = tmp / "run"
        run_dir.mkdir()

        (source / "config.json").write_text(
            json.dumps({"color_depth": "16"}), encoding="utf-8"
        )
        team_cfg = {"delivery_mode": "tracked", "records_backend": "repository"}
        (profiles_dir / "team.json").write_text(json.dumps(team_cfg), encoding="utf-8")
        orig_team_bytes = (profiles_dir / "team.json").read_bytes()

        item = {"position": 1, "id6": "qi5ljl"}
        handle = runner_shared.prepare_agent_user_config(
            run_dir, item, attempt_no=1, suffix="", source_dir=source
        )
        assert handle is not None
        assert handle.path.is_dir()

        sandbox_team = handle.path / "profiles" / "team.json"
        assert sandbox_team.is_file()
        assert sandbox_team.read_bytes() == orig_team_bytes

        # Modify profiles/team.json in the sandbox
        modified_team_cfg = {
            "delivery_mode": "clean-delta",
            "records_backend": "companion",
        }
        sandbox_team.write_text(json.dumps(modified_team_cfg), encoding="utf-8")

        records = runner_shared.reconcile_agent_user_config(handle, run_dir, item)
        mod_records = [r for r in records if r.get("file") == "profiles/team.json"]
        assert len(mod_records) == 1
        assert mod_records[0]["change"] == "modified"
        assert "records_backend" in mod_records[0].get("keys", [])

        # Source file is unchanged
        assert (profiles_dir / "team.json").read_bytes() == orig_team_bytes
