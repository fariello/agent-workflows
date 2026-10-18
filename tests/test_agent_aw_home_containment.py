"""Behavioral tests for agent AW_HOME containment (IPD 1vwjdl).

P16: behavioral only (drive code, assert outputs and side effects; no source reading).
Cells:
(a) find_project honors AW_HOME
(b) Registry seeding and discard of added, removed, or modified registry
(c) Discard of an incidental scratch project mint_run_dir
(d) Pass-through for home backend, clean-delta, and lane agent_dir
(e) Self-containing run dir reachable through sandbox link
(f) Fail-open when symlink creation fails
(g) report_discarded_aw_home output and silence
E-07: End-to-end runner tests for OpenCode and Antigravity, including prepare returning None.
"""

from __future__ import annotations

import io
import json
import os
import tempfile
from pathlib import Path
from unittest import mock

import pytest

from agent_workflows import (
    agy_runipd,
    oc_runipd,
    project_context,
    project_registry,
    runner_shared,
)
from tests import support

_REPO_ROOT = Path(__file__).resolve().parent.parent


def _can_symlink() -> bool:
    try:
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "src"
            src.mkdir()
            dst = Path(td) / "dst"
            os.symlink(src, dst, target_is_directory=True)
            return True
    except OSError:
        return False


SYMLINK_SUPPORTED = _can_symlink()
requires_symlink = pytest.mark.skipif(
    not SYMLINK_SUPPORTED,
    reason="os.symlink requires Developer Mode or Administrator on Windows",
)


def test_find_project_honors_aw_home():
    """Cell (a): find_project honors AW_HOME when aw_home and registry_data omitted."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir).resolve()
        aw_home = tmp / "aw_home"
        cfg = aw_home / "config"
        cfg.mkdir(parents=True)
        repo = tmp / "my_repo"
        repo.mkdir()

        reg_data = {
            "projects": {
                "proj-123": {
                    "project_id": "proj-123",
                    "human_slug": "proj",
                    "common_dir": str(repo),
                    "target_paths": [str(repo)],
                }
            }
        }
        (cfg / "registry.json").write_text(json.dumps(reg_data), encoding="utf-8")

        with mock.patch.dict(os.environ, {"AW_HOME": str(aw_home)}):
            match = project_registry.find_project(str(repo))
            assert match.match_kind is not None
            assert match.entry is not None
            assert match.entry.project_id == "proj-123"

        # When AW_HOME is unset and not passed, find_project falls back to ~/.aw
        with mock.patch.dict(os.environ, {}, clear=True):
            match_none = project_registry.find_project(str(repo))
            # ~/.aw won't have this random temp repo registered
            assert match_none.match_kind is None


def test_registry_seeding_and_discard_changes():
    """Cell (b): Registry seeding, plus discard of modified, added, removed registry.

    Events carry key names and no path or timestamp values.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir).resolve()
        real_home = tmp / "real_aw"
        (real_home / "config").mkdir(parents=True)
        orig_reg = {
            "projects": {
                "p1": {"project_id": "p1", "target_paths": ["/tmp/p1"]},
                "p2": {"project_id": "p2", "target_paths": ["/tmp/p2"]},
            },
            "operator_setting": "keep_this",
        }
        reg_file = real_home / "config" / "registry.json"
        reg_file.write_text(json.dumps(orig_reg), encoding="utf-8")
        orig_bytes = reg_file.read_bytes()

        run_dir = tmp / "run"
        run_dir.mkdir()
        item = {"position": 1, "id6": "1vwjdl"}

        # Subtest 1: modified registry
        handle = runner_shared.prepare_agent_aw_home(
            run_dir, item, 1, suffix="mod", source_dir=real_home
        )
        assert handle is not None
        assert "config/registry.json" in handle.seed_hashes
        assert handle.seed_json["config/registry.json"] == orig_reg

        # Agent modifies registry: adds top-level key, modifies p2, adds p3
        sb_reg_file = handle.path / "config" / "registry.json"
        modified_reg = {
            "projects": {
                "p1": {"project_id": "p1", "target_paths": ["/tmp/p1"]},
                "p2": {"project_id": "p2", "target_paths": ["/tmp/p2_changed"]},
                "p3": {"project_id": "p3", "target_paths": ["/tmp/p3"]},
            },
            "operator_setting": "keep_this",
            "agent_incidental_key": "val",
        }
        sb_reg_file.write_text(json.dumps(modified_reg), encoding="utf-8")

        recs = runner_shared.reconcile_agent_aw_home(handle, run_dir, item)
        assert reg_file.read_bytes() == orig_bytes
        assert not handle.path.exists()

        mod_recs = [r for r in recs if r["file"] == "config/registry.json"]
        assert len(mod_recs) == 1
        ev = mod_recs[0]
        assert ev["change"] == "modified"
        assert ev["keys"] == ["agent_incidental_key", "projects.p2", "projects.p3"]
        # Ensure values like /tmp/p2_changed or 'val' are NOT in keys
        assert "/tmp/p2_changed" not in str(ev["keys"])
        assert "val" not in str(ev["keys"])

        # Subtest 2: added registry (real home started with no registry)
        real_empty_home = tmp / "empty_aw"
        real_empty_home.mkdir()
        handle2 = runner_shared.prepare_agent_aw_home(
            run_dir, item, 2, suffix="add", source_dir=real_empty_home
        )
        assert handle2 is not None
        assert "config/registry.json" not in handle2.seed_hashes
        (handle2.path / "config" / "registry.json").write_text("{}", encoding="utf-8")

        recs2 = runner_shared.reconcile_agent_aw_home(handle2, run_dir, item)
        assert not (real_empty_home / "config" / "registry.json").exists()
        assert not handle2.path.exists()
        add_recs = [r for r in recs2 if r["file"] == "config/registry.json"]
        assert len(add_recs) == 1
        assert add_recs[0]["change"] == "added"

        # Subtest 3: removed registry (agent unlinks registry)
        handle3 = runner_shared.prepare_agent_aw_home(
            run_dir, item, 3, suffix="rem", source_dir=real_home
        )
        assert handle3 is not None
        (handle3.path / "config" / "registry.json").unlink()

        recs3 = runner_shared.reconcile_agent_aw_home(handle3, run_dir, item)
        assert reg_file.read_bytes() == orig_bytes
        assert not handle3.path.exists()
        rem_recs = [r for r in recs3 if r["file"] == "config/registry.json"]
        assert len(rem_recs) == 1
        assert rem_recs[0]["change"] == "removed"


def test_incidental_scratch_project_discard():
    """Cell (c): Discard of incidental scratch project mint_run_dir under sandbox AW_HOME."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir).resolve()
        real_home = tmp / "real_aw"
        (real_home / "config").mkdir(parents=True)
        (real_home / "projects").mkdir(parents=True)
        reg_file = real_home / "config" / "registry.json"
        reg_file.write_text("{}", encoding="utf-8")

        run_dir = tmp / "run"
        run_dir.mkdir()
        item = {"position": 1, "id6": "1vwjdl"}

        handle = runner_shared.prepare_agent_aw_home(
            run_dir, item, 1, suffix="scratch", source_dir=real_home
        )
        assert handle is not None

        # Simulate agent turn running mint_run_dir against an unconfigured scratch dir
        scratch_repo = tmp / "scratch_work"
        scratch_repo.mkdir()

        with mock.patch.dict(os.environ, {"AW_HOME": str(handle.path)}):
            _, scratch_run_dir = runner_shared.mint_run_dir(scratch_repo)

        # The scratch run dir was created inside the sandbox AW_HOME
        assert str(scratch_run_dir).startswith(str(handle.path))

        ctx = project_context.resolve_project_context(
            target_repo=str(scratch_repo), aw_home=str(handle.path)
        )
        scratch_pid = ctx.project_id

        # Reconcile turn
        recs = runner_shared.reconcile_agent_aw_home(handle, run_dir, item)
        assert not (real_home / "projects" / scratch_pid).exists()
        assert not handle.path.exists()

        scratch_recs = [r for r in recs if r["file"] == f"projects/{scratch_pid}"]
        assert len(scratch_recs) == 1
        assert scratch_recs[0]["change"] == "added"
        assert "records" in scratch_recs[0]["keys"]


@requires_symlink
def test_pass_through_home_clean_delta_and_lane_agent_dir():
    """Cell (d): Pass-through for home-backend, clean-delta, and lane agent_dir."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir).resolve()
        real_home = tmp / "real_aw"
        (real_home / "config").mkdir(parents=True)
        (real_home / "projects").mkdir(parents=True)
        reg_file = real_home / "config" / "registry.json"
        reg_file.write_text("{}", encoding="utf-8")
        orig_reg_bytes = reg_file.read_bytes()

        run_dir = tmp / "run"
        run_dir.mkdir()
        item = {"position": 1, "id6": "1vwjdl"}

        # 1. Configured records_backend: home repo
        repo_home = tmp / "repo_home"
        (repo_home / ".aw" / "config").mkdir(parents=True)
        (repo_home / ".aw" / "config" / "project.json").write_text(
            json.dumps({"records_backend": "home"}), encoding="utf-8"
        )
        ctx_home = project_context.resolve_project_context(
            target_repo=str(repo_home), aw_home=str(real_home)
        )
        pid_home = ctx_home.project_id

        # 2. Configured delivery_mode: clean-delta repo
        repo_clean = tmp / "repo_clean"
        repo_clean.mkdir()
        pid_clean = project_context._derive_project_id(str(repo_clean))
        clean_cfg_dir = real_home / "projects" / pid_clean / "config"
        clean_cfg_dir.mkdir(parents=True)
        (clean_cfg_dir / "project.json").write_text(
            json.dumps({"delivery_mode": "clean-delta", "records_backend": "home"}),
            encoding="utf-8",
        )

        # 3. Lane agent_dir with its own pid
        lane_wt = tmp / "lane_worktree"
        (lane_wt / ".aw" / "config").mkdir(parents=True)
        (lane_wt / ".aw" / "config" / "project.json").write_text(
            json.dumps({"records_backend": "home"}), encoding="utf-8"
        )
        ctx_lane = project_context.resolve_project_context(
            target_repo=str(lane_wt), aw_home=str(real_home)
        )
        pid_lane = ctx_lane.project_id

        # Prepare sandbox for repo_home and lane_wt
        handle = runner_shared.prepare_agent_aw_home(
            run_dir,
            item,
            1,
            suffix="pt1",
            source_dir=real_home,
            repo=repo_home,
            agent_dir=lane_wt,
        )
        assert handle is not None
        assert pid_home in handle.linked_projects
        assert pid_lane in handle.linked_projects

        # Legitimate writes via pass-through
        home_write = handle.path / "projects" / pid_home / "records" / "note.txt"
        home_write.parent.mkdir(parents=True, exist_ok=True)
        home_write.write_text("hello home", encoding="utf-8")

        lane_write = handle.path / "projects" / pid_lane / "records" / "lane.txt"
        lane_write.parent.mkdir(parents=True, exist_ok=True)
        lane_write.write_text("hello lane", encoding="utf-8")

        # Incidental scratch write
        incidental = handle.path / "projects" / "incidental-scratch" / "f"
        incidental.parent.mkdir(parents=True, exist_ok=True)
        incidental.write_text("pollute", encoding="utf-8")

        # Incidental registry write
        (handle.path / "config" / "registry.json").write_text(
            json.dumps({"bad": True}), encoding="utf-8"
        )

        recs = runner_shared.reconcile_agent_aw_home(handle, run_dir, item)
        assert len(recs) >= 1

        # Verified: legitimate writes landed at real location
        assert (real_home / "projects" / pid_home / "records" / "note.txt").read_text(
            encoding="utf-8"
        ) == "hello home"
        assert (real_home / "projects" / pid_lane / "records" / "lane.txt").read_text(
            encoding="utf-8"
        ) == "hello lane"

        # Verified: incidental writes discarded
        assert not (real_home / "projects" / "incidental-scratch").exists()
        assert reg_file.read_bytes() == orig_reg_bytes
        assert not handle.path.exists()

        # Check clean-delta repository as single target
        handle_cd = runner_shared.prepare_agent_aw_home(
            run_dir, item, 2, suffix="cd", source_dir=real_home, repo=repo_clean
        )
        assert handle_cd is not None
        assert pid_clean in handle_cd.linked_projects
        cd_write = handle_cd.path / "projects" / pid_clean / "records" / "cd.txt"
        cd_write.parent.mkdir(parents=True, exist_ok=True)
        cd_write.write_text("clean delta rec", encoding="utf-8")

        recs_cd = runner_shared.reconcile_agent_aw_home(handle_cd, run_dir, item)
        assert len(recs_cd) == 0
        assert (real_home / "projects" / pid_clean / "records" / "cd.txt").read_text(
            encoding="utf-8"
        ) == "clean delta rec"
        assert not handle_cd.path.exists()


@requires_symlink
def test_self_containing_run_dir():
    """Cell (e): run_dir under <real>/projects/<pid>/records/runs/ is reachable through link."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir).resolve()
        real_home = tmp / "real_aw"
        (real_home / "config").mkdir(parents=True)
        (real_home / "config" / "registry.json").write_text("{}", encoding="utf-8")

        repo = tmp / "repo"
        (repo / ".aw" / "config").mkdir(parents=True)
        (repo / ".aw" / "config" / "project.json").write_text(
            json.dumps({"records_backend": "home"}), encoding="utf-8"
        )
        ctx = project_context.resolve_project_context(
            target_repo=str(repo), aw_home=str(real_home)
        )
        pid = ctx.project_id

        run_dir = real_home / "projects" / pid / "records" / "runs" / "run-2026-test"
        run_dir.mkdir(parents=True)
        item = {"position": 1, "id6": "1vwjdl"}

        handle = runner_shared.prepare_agent_aw_home(
            run_dir, item, 1, suffix="self", source_dir=real_home, repo=repo
        )
        assert handle is not None

        # Existing real records file
        real_file = real_home / "projects" / pid / "records" / "prior_record.txt"
        real_file.write_text("prior", encoding="utf-8")

        recs = runner_shared.reconcile_agent_aw_home(handle, run_dir, item)
        assert len(recs) == 0
        assert not handle.path.exists()
        # Verify the real file was not deleted
        assert real_file.is_file()
        assert real_file.read_text(encoding="utf-8") == "prior"


def test_fail_open_on_symlink_error():
    """Cell (f): Fail-open when os.symlink raises OSError."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir).resolve()
        real_home = tmp / "real_aw"
        (real_home / "config").mkdir(parents=True)
        (real_home / "config" / "registry.json").write_text("{}", encoding="utf-8")

        repo = tmp / "repo"
        (repo / ".aw" / "config").mkdir(parents=True)
        (repo / ".aw" / "config" / "project.json").write_text(
            json.dumps({"records_backend": "home"}), encoding="utf-8"
        )

        run_dir = tmp / "run"
        run_dir.mkdir()
        item = {"position": 1, "id6": "1vwjdl"}

        with mock.patch("os.symlink", side_effect=OSError("Operation not permitted")):
            handle = runner_shared.prepare_agent_aw_home(
                run_dir, item, 1, suffix="failopen", source_dir=real_home, repo=repo
            )
            assert handle is None

        # Nothing was left behind in sandbox or created under real projects
        assert not (run_dir / "agent-aw-home" / "01-1vwjdl-attempt-1-failopen").exists()
        assert (
            not (real_home / "projects").exists()
            or list((real_home / "projects").iterdir()) == []
        )


def test_report_discarded_aw_home_output_and_silence():
    """Cell (g): report_discarded_aw_home output and silence when there are no events."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir).resolve()
        run_dir = tmp / "run"
        run_dir.mkdir()

        # Silence when no events file
        buf_empty = io.StringIO()
        res_empty = runner_shared.report_discarded_aw_home(run_dir, stream=buf_empty)
        assert res_empty == []
        assert buf_empty.getvalue() == ""

        # With events in events.jsonl
        events_file = run_dir / "events.jsonl"
        ev1 = {
            "at": "2026-10-16T00:00:00+00:00",
            "event": "agent-aw-home-discarded",
            "id6": "1vwjdl",
            "attempt": 1,
            "file": "config/registry.json",
            "change": "modified",
            "keys": ["agent_key"],
        }
        ev2 = {
            "at": "2026-10-16T00:00:00+00:00",
            "event": "agent-aw-home-discarded",
            "id6": "1vwjdl",
            "attempt": 1,
            "file": "projects/scratch-abc",
            "change": "added",
            "keys": ["records"],
        }
        ev_unrelated = {
            "at": "2026-10-16T00:00:00+00:00",
            "event": "unrelated-event",
        }
        runner_shared.append_jsonl(events_file, ev1)
        runner_shared.append_jsonl(events_file, ev2)
        runner_shared.append_jsonl(events_file, ev_unrelated)

        buf = io.StringIO()
        res = runner_shared.report_discarded_aw_home(run_dir, stream=buf)
        assert len(res) == 1
        output = buf.getvalue().strip()
        assert output.startswith("Agent AW_HOME changes discarded: 2")
        assert "1vwjdl: config/registry.json ['agent_key']" in output
        assert "1vwjdl: projects/scratch-abc ['records']" in output


def test_incident_end_to_end_per_host(capsys):
    """E-07: The incident end-to-end per host (oc_runipd and agy_runipd).

    Fake agent executable writes a new key into $AW_HOME/config/registry.json and creates
    $AW_HOME/projects/scratch-x/f.
    Asserts real registry bytes unchanged, <real>/projects/scratch-x absent,
    agent-aw-home-discarded event exists, stderr carries DISCARDED line, sandbox deleted.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir).resolve()
        real_aw = tmp / "real_aw"
        (real_aw / "config").mkdir(parents=True)
        (real_aw / "projects").mkdir(parents=True)
        real_reg = real_aw / "config" / "registry.json"
        initial_reg = {"projects": {"existing": {"project_id": "existing"}}}
        real_reg.write_text(json.dumps(initial_reg), encoding="utf-8")
        orig_bytes = real_reg.read_bytes()

        # Fake agent executable
        script = support.make_fake_executable(
            tmp / "fake_agent",
            """#!/usr/bin/env python3
import json, os, sys
from pathlib import Path

aw_home = Path(os.environ["AW_HOME"])
reg_path = aw_home / "config" / "registry.json"
if reg_path.is_file():
    data = json.loads(reg_path.read_text(encoding="utf-8"))
else:
    data = {}
data["agent_probe_key"] = "forbidden"
(aw_home / "config").mkdir(parents=True, exist_ok=True)
reg_path.write_text(json.dumps(data), encoding="utf-8")

scratch_dir = aw_home / "projects" / "scratch-x"
scratch_dir.mkdir(parents=True, exist_ok=True)
(scratch_dir / "f").write_text("scratch", encoding="utf-8")
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
            "run_id": "run-test-aw-home-incident",
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
        item = {"position": 1, "id6": "1vwjdl", "setid": "s4pys7"}

        with mock.patch.dict(os.environ, {"AW_HOME": str(real_aw)}):
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
            assert real_reg.read_bytes() == orig_bytes
            assert not (real_aw / "projects" / "scratch-x").exists()
            captured = capsys.readouterr()
            assert "DISCARDED" in captured.err
            assert "IPD 1vwjdl: agent changed AW_HOME" in captured.err
            assert not (run_dir / "agent-aw-home").exists() or not any(
                (run_dir / "agent-aw-home").iterdir()
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
                ev for ev in lines if ev.get("event") == "agent-aw-home-discarded"
            ]
            assert (
                len(discard_lines) == 2
            )  # config/registry.json and projects/scratch-x
            reg_ev = next(
                ev for ev in discard_lines if ev["file"] == "config/registry.json"
            )
            assert reg_ev["keys"] == ["agent_probe_key"]
            scratch_ev = next(
                ev for ev in discard_lines if ev["file"] == "projects/scratch-x"
            )
            assert scratch_ev["keys"] == ["f"]

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
            assert real_reg.read_bytes() == orig_bytes
            assert not (real_aw / "projects" / "scratch-x").exists()
            captured_agy = capsys.readouterr()
            assert "DISCARDED" in captured_agy.err
            assert "IPD 1vwjdl: agent changed AW_HOME" in captured_agy.err
            assert not (run_dir / "agent-aw-home").exists() or not any(
                (run_dir / "agent-aw-home").iterdir()
            )


def test_prepare_none_inherits_driver_aw_home_per_host():
    """E-07: When prepare_agent_aw_home returns None, child observes inherited AW_HOME unchanged."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir).resolve()
        driver_aw_home = tmp / "driver_aw_home"
        driver_aw_home.mkdir()
        observed_oc = tmp / "observed_oc.txt"
        observed_agy = tmp / "observed_agy.txt"

        script_oc = support.make_fake_executable(
            tmp / "agent_oc",
            f"""#!/usr/bin/env python3
import os
from pathlib import Path
Path({str(observed_oc)!r}).write_text(os.environ.get("AW_HOME", "UNSET"), encoding="utf-8")
""",
        )
        script_agy = support.make_fake_executable(
            tmp / "agent_agy",
            f"""#!/usr/bin/env python3
import os
from pathlib import Path
Path({str(observed_agy)!r}).write_text(os.environ.get("AW_HOME", "UNSET"), encoding="utf-8")
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
            "run_id": "run-test-inherit-aw-home",
            "repo": str(tmp),
            "options": {
                "opencode": str(script_oc),
                "agy_executable": str(script_agy),
                "stall_timeout": 10.0,
                "timeout": 10.0,
                "output_mode": "raw",
            },
            "queue": [],
        }
        item = {"position": 1, "id6": "1vwjdl", "setid": "s4pys7"}

        with (
            mock.patch.dict(os.environ, {"AW_HOME": str(driver_aw_home)}),
            mock.patch(
                "agent_workflows.runner_shared.prepare_agent_aw_home",
                return_value=None,
            ),
        ):
            # 1. OpenCode
            rc_oc, _, _, _ = oc_runipd.run_opencode(
                state=state,
                run_dir=run_dir,
                item=item,
                plan_path=plan_path,
                prompt_path=prompt_path,
                attempt_no=1,
            )
            assert rc_oc == 0
            assert observed_oc.read_text(encoding="utf-8").strip() == str(
                driver_aw_home
            )

            # 2. Antigravity
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
            assert observed_agy.read_text(encoding="utf-8").strip() == str(
                driver_aw_home
            )
