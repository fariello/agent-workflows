"""Behavioral tests for residual runner, lane, storage, telemetry, and push-gate helpers.

Provenance:
- Backlog item: nzc6dm
- Plan: sbcmke
- Findings: wo21z5

Direct behavioral coverage for:
- runner_shared.attributed_away_failure_ids
- worktree_lease.lane_id_from_branch
- storage.get_git_common_dir
- run_analytics_telemetry.TelemetryCollector._observe_tool_versions
- check_engine.check_push_authorization / hooks.prepush_authorization_gate.check
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

from agent_workflows import (
    check_engine,
    run_analytics_telemetry,
    runner_shared,
    storage,
    worktree_lease,
)
from agent_workflows.hooks import prepush_authorization_gate

pytestmark = pytest.mark.core


class AttributedAwayFailureIdsTests:
    __test__ = True

    def test_attributed_away_failure_ids_usable_not_mine(self) -> None:
        key = runner_shared.GATE_ANSWER_RECORD_KEY
        item = {
            key: {
                "answer": "not-mine",
                "usable": True,
                "failing_tests": [
                    "FAILED tests/test_a.py::T::test_x - boom",
                    "FAILED tests/test_b.py::test_y",
                    "FAILED tests/test_a.py::T::test_x - again",
                    "garbage line ???",
                ],
            }
        }
        assert runner_shared.attributed_away_failure_ids(item) == (
            "FAILED tests/test_a.py::T::test_x",
            "FAILED tests/test_b.py::test_y",
        )

    def test_attributed_away_failure_ids_mine(self) -> None:
        key = runner_shared.GATE_ANSWER_RECORD_KEY
        item = {
            key: {
                "answer": "mine",
                "usable": True,
                "failing_tests": [
                    "FAILED tests/test_a.py::T::test_x - boom",
                ],
            }
        }
        assert runner_shared.attributed_away_failure_ids(item) == ()

    def test_attributed_away_failure_ids_unusable(self) -> None:
        key = runner_shared.GATE_ANSWER_RECORD_KEY
        item = {
            key: {
                "answer": "not-mine",
                "usable": False,
                "failing_tests": [
                    "FAILED tests/test_a.py::T::test_x - boom",
                ],
            }
        }
        assert runner_shared.attributed_away_failure_ids(item) == ()

    def test_attributed_away_failure_ids_bare_string(self) -> None:
        key = runner_shared.GATE_ANSWER_RECORD_KEY
        item = {
            key: {
                "answer": "not-mine",
                "usable": True,
                "failing_tests": "FAILED tests/test_a.py::T::test_x - boom",
            }
        }
        assert runner_shared.attributed_away_failure_ids(item) == ()

    def test_attributed_away_failure_ids_missing_record(self) -> None:
        assert runner_shared.attributed_away_failure_ids({}) == ()


class LaneIdFromBranchTests:
    __test__ = True

    def test_lane_id_from_branch(self) -> None:
        assert worktree_lease.lane_id_from_branch("aw/lane/ntf6sx") == "ntf6sx"
        assert (
            worktree_lease.lane_id_from_branch("aw/lane/abc123_attempt2")
            == "abc123_attempt2"
        )
        assert worktree_lease.lane_id_from_branch("aw/lane/") is None
        assert worktree_lease.lane_id_from_branch("main") is None
        assert worktree_lease.lane_id_from_branch("") is None


class GitCommonDirTests:
    __test__ = True

    def test_git_common_dir(self, tmp_path: Path) -> None:
        repo_dir = tmp_path / "repo"
        repo_dir.mkdir()
        subprocess.run(["git", "init", "-q", "-b", "main"], cwd=repo_dir, check=True)
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=repo_dir,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Tester"], cwd=repo_dir, check=True
        )
        subprocess.run(
            ["git", "config", "commit.gpgsign", "false"], cwd=repo_dir, check=True
        )
        (repo_dir / "sample.txt").write_text("content", encoding="utf-8")
        subprocess.run(["git", "add", "sample.txt"], cwd=repo_dir, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=repo_dir, check=True)

        wt_dir = tmp_path / "worktree"
        subprocess.run(
            ["git", "worktree", "add", "-q", str(wt_dir)], cwd=repo_dir, check=True
        )

        non_git_dir = tmp_path / "nongit"
        non_git_dir.mkdir()

        expected = os.path.realpath(repo_dir / ".git")
        assert storage.get_git_common_dir(repo_dir) == expected
        assert storage.get_git_common_dir(wt_dir) == expected
        assert storage.get_git_common_dir(non_git_dir) is None


class TelemetryToolVersionsTests:
    __test__ = True

    def test_telemetry_tool_versions_observed_in_start_event(
        self, tmp_path: Path
    ) -> None:
        collector = run_analytics_telemetry.TelemetryCollector(
            tmp_path / "s1.jsonl",
            execution_id="e1",
            salt="s",
            adapter=run_analytics_telemetry.FakeResourceProbeAdapter(
                tool_versions=run_analytics_telemetry.ProbeOutcome(
                    "ok", {"python": "3.14.0"}
                )
            ),
        )
        try:
            event = collector.start()
            assert event is not None
            assert event["event_kind"] == "start"
            assert event["tool_versions"] == {"python": "3.14.0"}
        finally:
            collector.close()

    def test_telemetry_tool_versions_unavailable(self, tmp_path: Path) -> None:
        collector = run_analytics_telemetry.TelemetryCollector(
            tmp_path / "s2.jsonl",
            execution_id="e2",
            salt="s",
            adapter=run_analytics_telemetry.FakeResourceProbeAdapter(
                tool_versions=run_analytics_telemetry.ProbeOutcome("unavailable")
            ),
        )
        try:
            event = collector.start()
            assert event is not None
            assert "tool_versions" not in event
        finally:
            collector.close()

    def test_telemetry_tool_versions_probe_raises(self, tmp_path: Path) -> None:
        class RaisingAdapter(run_analytics_telemetry.FakeResourceProbeAdapter):
            def tool_versions(self) -> run_analytics_telemetry.ProbeOutcome:
                raise RuntimeError("probe failed")

        collector = run_analytics_telemetry.TelemetryCollector(
            tmp_path / "s3.jsonl",
            execution_id="e3",
            salt="s",
            adapter=RaisingAdapter(),
        )
        try:
            event = collector.start()
            assert event is not None
            assert "tool_versions" not in event
        finally:
            collector.close()


class PushAuthorizationGateTests:
    __test__ = True

    def test_prepush_gate_check_unauthorized(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv(check_engine.PUSH_ACK_ENV, raising=False)
        code, msgs = prepush_authorization_gate.check(tmp_path)
        assert code == 1
        assert len(msgs) == 1
        assert "check.push-unauthorized" in msgs[0]
        assert f"{check_engine.PUSH_ACK_ENV}=1" in msgs[0]

    def test_prepush_gate_check_authorized(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv(check_engine.PUSH_ACK_ENV, "1")
        code, msgs = prepush_authorization_gate.check(tmp_path)
        assert code == 0
        assert msgs == []

    def test_check_push_authorization_direct(self, tmp_path: Path) -> None:
        drifts_unack = check_engine.check_push_authorization(tmp_path, ack=False)
        assert len(drifts_unack) == 1
        assert drifts_unack[0].rule == "check.push-unauthorized"
        assert drifts_unack[0].location == "<push>"

        drifts_ack = check_engine.check_push_authorization(tmp_path, ack=True)
        assert drifts_ack == []
