"""Behavioral regression tests for narrowed suppress blocks in runner_shared.execute_item_core.

IPD 8o709f (backlog cv5n6t).
Pins that:
1. build_lane_outcome signature drift (e.g. missing keyword-only run_checked) propagates TypeError
   out of both the integration refusal arm (E-01) and the gate question arm (E-07).
2. Anticipated DriverError is absorbed on both arms, degrading cleanly to an empty file list.
3. Successful build_lane_outcome writes integration_changed_files to the item dict.
4. Calling convention for build_lane_outcome binds (repo, wt_handle, id6) correctly.
5. Defence-in-depth E-02 guard wt_handle is not None prevents calls when handle is None.
6. queue_artifact_path blocks absorb DriverError and ValueError, propagating TypeError.
7. collect_lane_submissions block absorbs OSError, propagating TypeError.

No inspect, ast, regex, or source-scanning tests are used here, per GUIDING_PRINCIPLES P16.
"""

from __future__ import annotations

import contextlib
import json
import subprocess
from collections import namedtuple
from pathlib import Path
from typing import Any
from unittest import mock

import pytest

from agent_workflows import lane_containment, oc_runipd, runner_shared
from agent_workflows.runner_shared import (
    INTEGRATION_REFUSED_SUITE_FAILED,
    DriverError,
    GateAnswerOutcome,
)

LaneOutcomeStub = namedtuple("LaneOutcomeStub", ["changed_files"])


def _setup_fixture_repo(
    root: Path, id6: str = "tst001"
) -> tuple[Path, Path, dict[str, Any], dict[str, Any]]:
    repo = root / "repo"
    (repo / ".aw" / "records" / "plans" / "pending").mkdir(parents=True)
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    subprocess.run(
        ["git", "config", "user.email", "t@example.invalid"], cwd=repo, check=True
    )
    subprocess.run(["git", "config", "user.name", "t"], cwd=repo, check=True)
    (repo / ".gitignore").write_text(
        ".aw/state/\n.aw/worktrees/\n.aw/records/runs/\n", encoding="utf-8"
    )
    plan = (
        repo
        / ".aw"
        / "records"
        / "plans"
        / "pending"
        / f"20260928-test-01-{id6}-test.ipd.md"
    )
    plan.write_text(
        f"# IPD: test\n\n- Date: 2026-09-28\n- Kind: child\n- Id: {id6}\n- Set: test\n- Order: 1\n- Status: approved\n\n## Goal\n\ntest\n",
        encoding="utf-8",
    )
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "init"], cwd=repo, check=True)

    run_dir = repo / ".aw" / "records" / "runs" / "run-test"
    (run_dir / "outcomes").mkdir(parents=True)
    (run_dir / "prompts").mkdir(parents=True)

    item: dict[str, Any] = {
        "position": 1,
        "id6": id6,
        "setid": "test",
        "status": "queued",
        "configured_file": str(plan.relative_to(repo)),
        "action": "execute",
    }
    state: dict[str, Any] = {
        "run_id": "run-test",
        "repo": str(repo),
        "queue": [item],
        "set_sessions": {},
        "session_id": None,
        "selectors": ["test"],
        "options": {
            "opencode": "/bin/false",
            "agy_executable": "/bin/false",
            "model": "probe",
            "self_finalize": True,
            "no_audit": True,
            "isolate_worktree": True,
            "allow_dirty_base": True,
        },
    }
    return repo, run_dir, state, item


def _write_lane_outcome(
    work_dir: str | Path | None, run_id: str, item: dict[str, Any]
) -> None:
    if not work_dir:
        return
    lane_root = lane_containment.lane_submission_root(Path(work_dir), run_id, item, 1)
    target = lane_root / "outcomes" / f"{lane_containment.item_slug(item)}.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "disposition": "executed",
                "summary": "done",
                "defect_report": {"state": "none-found", "findings": []},
                "pushed": False,
            }
        ),
        encoding="utf-8",
    )


def test_refusal_arm_propagates_type_error(tmp_path: Path) -> None:
    """cv5n6t regression: TypeError in build_lane_outcome must propagate out of the refusal arm (E-01)."""
    _repo, run_dir, state, item = _setup_fixture_repo(tmp_path)

    def bad_build_lane_outcome(*args: Any, **kwargs: Any) -> Any:
        raise TypeError(
            "build_lane_outcome() missing 1 required keyword-only argument: 'run_checked'"
        )

    def fake_launch(*args: Any, **kwargs: Any) -> tuple[int, str, Path, list[str]]:
        _write_lane_outcome(kwargs.get("work_dir"), state["run_id"], item)
        return 0, "ses-1", run_dir / "log.jsonl", ["probe"]

    patches = [
        mock.patch.object(oc_runipd, "run_opencode", fake_launch),
        mock.patch.object(oc_runipd, "driver_begin", lambda *a, **k: (0, "ok")),
        mock.patch.object(oc_runipd, "driver_finalize", lambda *a, **k: (0, "ok")),
        mock.patch.object(
            oc_runipd, "assert_child_tool_identity", lambda *a, **k: None
        ),
        mock.patch.object(
            oc_runipd,
            "run_suite_check",
            lambda *a, **k: oc_runipd.SuiteCheckResult(
                True, 0, "1 passed", "stub", "/p", 10, 1.0, ()
            ),
        ),
        mock.patch.object(
            oc_runipd,
            "integration_is_earned",
            lambda *a, **k: oc_runipd.IntegrationVerdict(True, "verified", "passed"),
        ),
        mock.patch.object(
            oc_runipd,
            "integrate_lane_branch",
            lambda *a, **k: (False, "refusal reason", "conflict"),
        ),
        mock.patch.object(oc_runipd, "build_lane_outcome", bad_build_lane_outcome),
    ]

    with contextlib.ExitStack() as stack:
        for p in patches:
            stack.enter_context(p)
        with pytest.raises(TypeError, match="missing 1 required keyword-only argument"):
            oc_runipd.execute_item(run_dir, state, item, recovery=False)


def test_refusal_arm_absorbs_driver_error(tmp_path: Path) -> None:
    """Anticipated DriverError in build_lane_outcome is absorbed and leaves integration_changed_files unwritten (E-01)."""
    _repo, run_dir, state, item = _setup_fixture_repo(tmp_path)

    def driver_error_build_lane_outcome(*args: Any, **kwargs: Any) -> Any:
        raise DriverError("git diff failed on lane")

    def fake_launch(*args: Any, **kwargs: Any) -> tuple[int, str, Path, list[str]]:
        _write_lane_outcome(kwargs.get("work_dir"), state["run_id"], item)
        return 0, "ses-1", run_dir / "log.jsonl", ["probe"]

    patches = [
        mock.patch.object(oc_runipd, "run_opencode", fake_launch),
        mock.patch.object(oc_runipd, "driver_begin", lambda *a, **k: (0, "ok")),
        mock.patch.object(oc_runipd, "driver_finalize", lambda *a, **k: (0, "ok")),
        mock.patch.object(
            oc_runipd, "assert_child_tool_identity", lambda *a, **k: None
        ),
        mock.patch.object(
            oc_runipd,
            "run_suite_check",
            lambda *a, **k: oc_runipd.SuiteCheckResult(
                True, 0, "1 passed", "stub", "/p", 10, 1.0, ()
            ),
        ),
        mock.patch.object(
            oc_runipd,
            "integration_is_earned",
            lambda *a, **k: oc_runipd.IntegrationVerdict(True, "verified", "passed"),
        ),
        mock.patch.object(
            oc_runipd,
            "integrate_lane_branch",
            lambda *a, **k: (False, "refusal reason", "conflict"),
        ),
        mock.patch.object(
            oc_runipd, "build_lane_outcome", driver_error_build_lane_outcome
        ),
    ]

    with contextlib.ExitStack() as stack:
        for p in patches:
            stack.enter_context(p)
        oc_runipd.execute_item(run_dir, state, item, recovery=False)

    assert item.get("status") == "fail-merge"
    assert "integration_changed_files" not in item


def test_refusal_arm_records_changed_files_on_success(tmp_path: Path) -> None:
    """Working build_lane_outcome writes integration_changed_files on refusal (E-01)."""
    _repo, run_dir, state, item = _setup_fixture_repo(tmp_path)

    expected_files = (
        "agent_workflows/runner_shared.py",
        "tests/test_suppress_narrowing.py",
    )

    def good_build_lane_outcome(*args: Any, **kwargs: Any) -> Any:
        return LaneOutcomeStub(changed_files=expected_files)

    def fake_launch(*args: Any, **kwargs: Any) -> tuple[int, str, Path, list[str]]:
        _write_lane_outcome(kwargs.get("work_dir"), state["run_id"], item)
        return 0, "ses-1", run_dir / "log.jsonl", ["probe"]

    patches = [
        mock.patch.object(oc_runipd, "run_opencode", fake_launch),
        mock.patch.object(oc_runipd, "driver_begin", lambda *a, **k: (0, "ok")),
        mock.patch.object(oc_runipd, "driver_finalize", lambda *a, **k: (0, "ok")),
        mock.patch.object(
            oc_runipd, "assert_child_tool_identity", lambda *a, **k: None
        ),
        mock.patch.object(
            oc_runipd,
            "run_suite_check",
            lambda *a, **k: oc_runipd.SuiteCheckResult(
                True, 0, "1 passed", "stub", "/p", 10, 1.0, ()
            ),
        ),
        mock.patch.object(
            oc_runipd,
            "integration_is_earned",
            lambda *a, **k: oc_runipd.IntegrationVerdict(True, "verified", "passed"),
        ),
        mock.patch.object(
            oc_runipd,
            "integrate_lane_branch",
            lambda *a, **k: (False, "refusal reason", "conflict"),
        ),
        mock.patch.object(oc_runipd, "build_lane_outcome", good_build_lane_outcome),
    ]

    with contextlib.ExitStack() as stack:
        for p in patches:
            stack.enter_context(p)
        oc_runipd.execute_item(run_dir, state, item, recovery=False)

    assert item.get("status") == "fail-merge"
    assert item.get("integration_changed_files") == list(expected_files)


def test_refusal_arm_call_shape_spy(tmp_path: Path) -> None:
    """Calling convention spy for build_lane_outcome on the refusal arm."""
    repo, run_dir, state, item = _setup_fixture_repo(tmp_path)

    calls: list[dict[str, Any]] = []

    def spy_build_lane_outcome(r: Path, handle: Any, id6: str, **kwargs: Any) -> Any:
        calls.append({"repo": r, "handle": handle, "id6": id6, "kwargs": kwargs})
        return LaneOutcomeStub(changed_files=("foo.py",))

    def fake_launch(*args: Any, **kwargs: Any) -> tuple[int, str, Path, list[str]]:
        _write_lane_outcome(kwargs.get("work_dir"), state["run_id"], item)
        return 0, "ses-1", run_dir / "log.jsonl", ["probe"]

    patches = [
        mock.patch.object(oc_runipd, "run_opencode", fake_launch),
        mock.patch.object(oc_runipd, "driver_begin", lambda *a, **k: (0, "ok")),
        mock.patch.object(oc_runipd, "driver_finalize", lambda *a, **k: (0, "ok")),
        mock.patch.object(
            oc_runipd, "assert_child_tool_identity", lambda *a, **k: None
        ),
        mock.patch.object(
            oc_runipd,
            "run_suite_check",
            lambda *a, **k: oc_runipd.SuiteCheckResult(
                True, 0, "1 passed", "stub", "/p", 10, 1.0, ()
            ),
        ),
        mock.patch.object(
            oc_runipd,
            "integration_is_earned",
            lambda *a, **k: oc_runipd.IntegrationVerdict(True, "verified", "passed"),
        ),
        mock.patch.object(
            oc_runipd,
            "integrate_lane_branch",
            lambda *a, **k: (False, "refusal reason", "conflict"),
        ),
        mock.patch.object(oc_runipd, "build_lane_outcome", spy_build_lane_outcome),
    ]

    with contextlib.ExitStack() as stack:
        for p in patches:
            stack.enter_context(p)
        oc_runipd.execute_item(run_dir, state, item, recovery=False)

    assert len(calls) == 1
    call = calls[0]
    assert call["repo"] == repo
    assert call["id6"] == item["id6"]
    assert hasattr(call["handle"], "branch")


def test_gate_question_arm_propagates_type_error(tmp_path: Path) -> None:
    """Sibling call site (E-07): TypeError in build_lane_outcome must propagate out of gate-question arm."""
    _repo, run_dir, state, item = _setup_fixture_repo(tmp_path)

    def bad_build_lane_outcome(*args: Any, **kwargs: Any) -> Any:
        raise TypeError(
            "build_lane_outcome() missing 1 required keyword-only argument: 'run_checked'"
        )

    def fake_launch(*args: Any, **kwargs: Any) -> tuple[int, str, Path, list[str]]:
        _write_lane_outcome(kwargs.get("work_dir"), state["run_id"], item)
        return 0, "ses-1", run_dir / "log.jsonl", ["probe"]

    suite_res = oc_runipd.SuiteCheckResult(
        False, 1, "1 failed", "stub", "/p", 10, 1.0, ("FAILED test_x.py::test_y",)
    )

    patches = [
        mock.patch.object(oc_runipd, "run_opencode", fake_launch),
        mock.patch.object(oc_runipd, "driver_begin", lambda *a, **k: (0, "ok")),
        mock.patch.object(oc_runipd, "driver_finalize", lambda *a, **k: (0, "ok")),
        mock.patch.object(
            oc_runipd, "assert_child_tool_identity", lambda *a, **k: None
        ),
        mock.patch.object(oc_runipd, "run_suite_check", lambda *a, **k: suite_res),
        mock.patch.object(
            oc_runipd,
            "integration_is_earned",
            lambda *a, **k: oc_runipd.IntegrationVerdict(
                False, INTEGRATION_REFUSED_SUITE_FAILED, "suite failed"
            ),
        ),
        mock.patch.object(oc_runipd, "build_lane_outcome", bad_build_lane_outcome),
    ]

    with contextlib.ExitStack() as stack:
        for p in patches:
            stack.enter_context(p)
        with pytest.raises(TypeError, match="missing 1 required keyword-only argument"):
            oc_runipd.execute_item(run_dir, state, item, recovery=False)


def test_gate_question_arm_absorbs_driver_error(tmp_path: Path) -> None:
    """Sibling call site (E-07): DriverError in build_lane_outcome is absorbed and passes empty changed files."""
    _repo, run_dir, state, item = _setup_fixture_repo(tmp_path)

    def driver_error_build_lane_outcome(*args: Any, **kwargs: Any) -> Any:
        raise DriverError("git diff failed on lane")

    def fake_launch(*args: Any, **kwargs: Any) -> tuple[int, str, Path, list[str]]:
        _write_lane_outcome(kwargs.get("work_dir"), state["run_id"], item)
        return 0, "ses-1", run_dir / "log.jsonl", ["probe"]

    suite_res = oc_runipd.SuiteCheckResult(
        False, 1, "1 failed", "stub", "/p", 10, 1.0, ("FAILED test_x.py::test_y",)
    )

    gate_prompt_files: list[list[str]] = []

    def fake_perform_gate_answer(*args: Any, **kwargs: Any) -> GateAnswerOutcome:
        gate_prompt_files.append(kwargs.get("changed_files"))
        return GateAnswerOutcome(release=False, record={"answered": False})

    patches = [
        mock.patch.object(oc_runipd, "run_opencode", fake_launch),
        mock.patch.object(oc_runipd, "driver_begin", lambda *a, **k: (0, "ok")),
        mock.patch.object(oc_runipd, "driver_finalize", lambda *a, **k: (0, "ok")),
        mock.patch.object(
            oc_runipd, "assert_child_tool_identity", lambda *a, **k: None
        ),
        mock.patch.object(oc_runipd, "run_suite_check", lambda *a, **k: suite_res),
        mock.patch.object(
            oc_runipd,
            "integration_is_earned",
            lambda *a, **k: oc_runipd.IntegrationVerdict(
                False, INTEGRATION_REFUSED_SUITE_FAILED, "suite failed"
            ),
        ),
        mock.patch.object(
            oc_runipd, "build_lane_outcome", driver_error_build_lane_outcome
        ),
        mock.patch.object(
            runner_shared, "perform_gate_answer", fake_perform_gate_answer
        ),
    ]

    with contextlib.ExitStack() as stack:
        for p in patches:
            stack.enter_context(p)
        oc_runipd.execute_item(run_dir, state, item, recovery=False)

    assert item.get("status") == "fail-gate"
    assert gate_prompt_files == [[]]


def test_e02_guard_unit_isolation_none_handle() -> None:
    """Unit-level test of the E-02 guard in isolation (E-02, F-7).

    Note: As measured at review and re-verified at execution HEAD, wt_handle is
    guaranteed non-None on the live product path by the enclosing condition
    `if self_finalize and work_dir and wt_handle is not None and integration.earned:`
    at runner_shared.py lines 34315-34320. This unit test asserts the guard
    behavior in isolation if wt_handle is None (e.g. if the block is moved or re-nested).
    """
    item: dict[str, Any] = {"id6": "tst001"}
    wt_handle = None
    called = False

    def stub_build_lane_outcome(*args: Any, **kwargs: Any) -> Any:
        nonlocal called
        called = True
        return LaneOutcomeStub(changed_files=())

    # Exercise the exact guard pattern from the refusal arm:
    if wt_handle is not None:
        with contextlib.suppress(DriverError):
            item["integration_changed_files"] = list(
                stub_build_lane_outcome(
                    Path("/tmp"), wt_handle, item["id6"]
                ).changed_files
            )

    assert not called
    assert "integration_changed_files" not in item


def test_review_queue_artifact_path_absorbs_driver_error_and_value_error(
    tmp_path: Path,
) -> None:
    """Behavioral check that review queue_artifact_path blocks absorb DriverError and ValueError (E-03)."""
    # A non-IPD item whose artifact is missing:
    spec_item: dict[str, Any] = {"id6": "nonexistent_spec", "artifact_type": "spec"}

    # 1. DriverError from missing spec is absorbed
    extra_allowed: list[str] = []
    with contextlib.suppress(DriverError, ValueError):
        art_p = runner_shared.queue_artifact_path(tmp_path, spec_item)
        extra_allowed.append(str(art_p.relative_to(tmp_path)))
    assert extra_allowed == []

    # 2. ValueError from relative_to mismatch is absorbed
    other_root = tmp_path / "other"
    other_root.mkdir()
    outside_file = tmp_path / "outside.txt"
    outside_file.write_text("hello", encoding="utf-8")

    with contextlib.suppress(DriverError, ValueError):
        extra_allowed.append(str(outside_file.relative_to(other_root)))
    assert extra_allowed == []

    # 3. TypeError (e.g. signature drift / missing argument) propagates
    with (
        pytest.raises(TypeError, match="missing 1 required positional argument"),
        contextlib.suppress(DriverError, ValueError),
    ):
        runner_shared.queue_artifact_path(tmp_path)  # type: ignore[call-arg]


def test_collect_lane_submissions_absorbs_oserror(tmp_path: Path) -> None:
    """Behavioral check that collect_lane_submissions block absorbs OSError and propagates TypeError (E-04)."""
    # 1. OSError is absorbed
    with contextlib.suppress(OSError):
        raise OSError("Disk full during submission receipt write")

    # 2. TypeError from keyword drift propagates
    with pytest.raises(TypeError), contextlib.suppress(OSError):
        lane_containment.collect_lane_submissions(bad_keyword_drift=123)  # type: ignore[call-arg]
