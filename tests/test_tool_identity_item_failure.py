"""Tests for item-local tool identity mismatch failure across both runners.

Plan: s2tn4q (backlog 03y5g6)
Spec: 25kzda 4.1
"""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path
from unittest import mock

import pytest

from agent_workflows import agy_runipd, oc_runipd, runner_shared
from agent_workflows.runner_shared import utc_now
from tests.test_oc_runipd import _CONFORMING_PLAN


def _init_repo_with_conforming_plan(repo: Path, id6: str = "itm001") -> Path:
    repo.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.invalid"], cwd=repo, check=True
    )
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
    (repo / ".gitignore").write_text(
        ".aw/state/\n.aw/worktrees/\n.aw/records/runs/\n", encoding="utf-8"
    )
    pending = repo / ".aw" / "records" / "plans" / "pending"
    pending.mkdir(parents=True)
    plan = pending / f"20260828-demo-01-{id6}-demo.ipd.md"
    plan.write_text(_CONFORMING_PLAN.format(id6=id6), encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "initial"], cwd=repo, check=True)
    return plan


@pytest.mark.parametrize("host,mod", [("oc", oc_runipd), ("agy", agy_runipd)])
def test_tool_identity_mismatch_fails_only_item_independent(host, mod):
    with tempfile.TemporaryDirectory() as temp:
        repo = Path(temp) / "repo"
        plan = _init_repo_with_conforming_plan(repo, "itm001")
        run_dir = repo / ".aw" / "records" / "runs" / "run-test"
        (run_dir / "outcomes").mkdir(parents=True)
        (run_dir / "prompts").mkdir(parents=True)

        state = {
            "run_id": "run-test",
            "created_at": "2026-08-28T00:00:00+00:00",
            "updated_at": "2026-08-28T00:00:00+00:00",
            "selectors": ["demo"],
            "repo": str(repo),
            "queue": [
                {
                    "position": 1,
                    "id6": "itm001",
                    "setid": "demo",
                    "status": "queued",
                    "configured_file": str(plan.relative_to(repo)),
                    "action": "execute",
                },
                {
                    "position": 2,
                    "id6": "itm002",
                    "setid": "demo",
                    "status": "queued",
                    "configured_file": str(plan.relative_to(repo)),
                    "action": "execute",
                },
            ],
            "options": {
                "model": "opus",
                "self_finalize": True,
                "isolate_worktree": False,
            },
        }
        mod.save_state(run_dir, state)

        dispatched = []

        def fake_execute(rd, st, it, *args, **kwargs):
            dispatched.append(it["id6"])
            if it["id6"] == "itm001":
                # Reproduce real begin-step precondition: open attempt, running, persisted
                attempt = {"number": 1, "started_at": utc_now()}
                it.setdefault("attempts", []).append(attempt)
                it["status"] = "running"
                mod.save_state(rd, st)
                raise runner_shared.ToolIdentityError(
                    "nested `aw` tool-identity mismatch; failing this item.\n"
                    "  expected module: /real/path/agent_workflows/__init__.py\n"
                    "  child resolved : /foreign/path/agent_workflows/__init__.py\n"
                    "  probe cwd      : /test/cwd\n"
                    "  child version  : 2.0.0\n"
                    "The item is failed without a fix-it turn, its dependents are cascaded, "
                    "independent items continue, and the remedy is to fix the runner's installation "
                    "(or PYTHONPATH) and resume with `--retry-incomplete`."
                )
            elif it["id6"] == "itm002":
                it["status"] = "executed"
                mod.save_state(rd, st)

        with mock.patch.object(mod, "execute_item", side_effect=fake_execute):
            exit_code = mod.run_queue(run_dir, retry_incomplete=False)

        assert dispatched == ["itm001", "itm002"]
        final_state = mod.load_state(run_dir)
        item1 = final_state["queue"][0]
        item2 = final_state["queue"][1]

        # Case (a) assertions:
        assert item1["status"] == "fail-gate"
        assert item1.get("refusal", {}).get("code") == "tool-identity-mismatch"
        assert "tool_identity_error" in item1
        last_attempt = item1["attempts"][-1]
        assert last_attempt.get("ended_at")
        assert last_attempt.get("disposition") == "fail-gate"

        assert item2["status"] == "executed"

        events_file = run_dir / "events.jsonl"
        assert events_file.exists()
        events = [
            json.loads(line)
            for line in events_file.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        failed_events = [
            e
            for e in events
            if e.get("event") == "ipd-tool-identity-failed" and e.get("id6") == "itm001"
        ]
        assert len(failed_events) == 1

        assert exit_code == 1


@pytest.mark.parametrize("host,mod", [("oc", oc_runipd), ("agy", agy_runipd)])
def test_tool_identity_mismatch_cascades_dependent_item(host, mod):
    with tempfile.TemporaryDirectory() as temp:
        repo = Path(temp) / "repo"
        plan = _init_repo_with_conforming_plan(repo, "itm001")
        run_dir = repo / ".aw" / "records" / "runs" / "run-test"
        (run_dir / "outcomes").mkdir(parents=True)
        (run_dir / "prompts").mkdir(parents=True)

        state = {
            "run_id": "run-test",
            "created_at": "2026-08-28T00:00:00+00:00",
            "updated_at": "2026-08-28T00:00:00+00:00",
            "selectors": ["demo"],
            "repo": str(repo),
            "queue": [
                {
                    "position": 1,
                    "id6": "itm001",
                    "setid": "demo",
                    "status": "queued",
                    "configured_file": str(plan.relative_to(repo)),
                    "action": "execute",
                },
                {
                    "position": 2,
                    "id6": "itm002",
                    "setid": "demo",
                    "status": "queued",
                    "dependencies": ["executed:itm001"],
                    "configured_file": str(plan.relative_to(repo)),
                    "action": "execute",
                },
            ],
            "options": {
                "model": "opus",
                "self_finalize": True,
                "isolate_worktree": False,
            },
        }
        mod.save_state(run_dir, state)

        dispatched = []

        def fake_execute(rd, st, it, *args, **kwargs):
            dispatched.append(it["id6"])
            if it["id6"] == "itm001":
                attempt = {"number": 1, "started_at": utc_now()}
                it.setdefault("attempts", []).append(attempt)
                it["status"] = "running"
                mod.save_state(rd, st)
                raise runner_shared.ToolIdentityError(
                    "nested `aw` tool-identity mismatch; failing this item"
                )
            else:
                it["status"] = "executed"
                mod.save_state(rd, st)

        with mock.patch.object(mod, "execute_item", side_effect=fake_execute):
            exit_code = mod.run_queue(run_dir, retry_incomplete=False)

        assert exit_code != 0
        assert dispatched == ["itm001"]
        final_state = mod.load_state(run_dir)
        item1 = final_state["queue"][0]
        item2 = final_state["queue"][1]

        assert item1["status"] == "fail-gate"
        assert item2["status"] in ("fail-depend", "dependency-blocked")


def test_assert_child_tool_identity_message_and_memo():
    with tempfile.TemporaryDirectory() as temp:
        repo = Path(temp) / "repo"
        repo.mkdir(parents=True, exist_ok=True)
        events_path = repo / "events.jsonl"

        snapshot = dict(runner_shared._TOOL_IDENTITY_VERIFIED)
        runner_shared._TOOL_IDENTITY_VERIFIED.clear()
        try:
            with mock.patch.object(runner_shared.subprocess, "run") as mock_run:
                mock_run.return_value = subprocess.CompletedProcess(
                    args=["fake"],
                    returncode=0,
                    stdout="/foreign/path/agent_workflows/__init__.py\n2.0.0\n",
                    stderr="",
                )
                with pytest.raises(runner_shared.ToolIdentityError) as exc_info:
                    runner_shared.assert_child_tool_identity(
                        events_path=events_path, cwd=repo
                    )

                err_msg = str(exc_info.value)
                assert "ABORTING RUN" not in err_msg
                assert "failing this item" in err_msg

                assert events_path.exists()
                events = [
                    json.loads(line)
                    for line in events_path.read_text(encoding="utf-8").splitlines()
                    if line.strip()
                ]
                mismatch_events = [
                    e for e in events if e.get("event") == "tool-identity-mismatch"
                ]
                assert len(mismatch_events) == 1

                assert not runner_shared._TOOL_IDENTITY_VERIFIED
        finally:
            runner_shared._TOOL_IDENTITY_VERIFIED.clear()
            runner_shared._TOOL_IDENTITY_VERIFIED.update(snapshot)
