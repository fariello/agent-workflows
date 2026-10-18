"""Tests for budget-only revalidation classification, caching, routing, and detection.

Plan: sa629y (backlog o58dro)
Tasks: E-04, E-05
"""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
from typing import Any
from unittest import mock

import pytest

from agent_workflows import runner_shared
from tests import support


@pytest.fixture
def repo_fixture(
    tmp_path: Path,
) -> tuple[Path, str, dict[str, Any], dict[str, Any], Path]:
    repo = support.init_repo(tmp_path / "seam_repo")
    (repo / "sample.txt").write_text("hello\n", encoding="utf-8")
    support.git(repo, "add", "-A", env=support.clean_git_env())
    support.git(repo, "commit", "-m", "init", env=support.clean_git_env())

    head = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()

    run_dir = tmp_path / "run_dir"
    run_dir.mkdir(parents=True, exist_ok=True)

    state: dict[str, Any] = {
        "repo": str(repo),
        "run_id": "run-o58dro01",
        "options": {"validate": False},
    }
    item: dict[str, Any] = {
        "id6": "o58dro",
        "base_commit": head,
        "lane_head": head,
        "attempts": [],
    }
    return repo, head, state, item, run_dir


def _make_suite_check_result(
    repo: Path,
    *,
    passing: bool,
    exit_code: int,
    failures: tuple[str, ...] = (),
    budget_only: bool = False,
    reason: str = "",
) -> runner_shared.SuiteCheckResult:
    return runner_shared.SuiteCheckResult(
        passing=passing,
        exit_code=exit_code,
        summary="summary",
        reason=reason or ("budget exceeded" if budget_only else "failed"),
        cwd=str(repo),
        timeout_seconds=60.0,
        elapsed_seconds=1.0,
        failures=failures,
        cached=False,
        digest="digest123",
        slot=None,
        budget_only=budget_only,
    )


def test_case_a_budget_only_red_is_unmeasured(
    repo_fixture: tuple[Path, str, dict[str, Any], dict[str, Any], Path],
) -> None:
    """(a) budget_only=True, passing=False, exit_code=1, failures=()
    -> runner returns False, record measured is False, 'budget' in reason,
    no baseline_comparison key, and runner_shared.revalidation_was_unmeasured(item) is True.
    """
    repo, _head, state, item, run_dir = repo_fixture
    stub_result = _make_suite_check_result(
        repo,
        passing=False,
        exit_code=1,
        failures=(),
        budget_only=True,
        reason="core tier wall-time budget exceeded",
    )
    runner = runner_shared.make_integration_validation_runner(
        state,
        run_dir,
        item,
        suite_check=lambda _p, _r: stub_result,
    )
    verdict = runner("", ["x"])
    assert verdict is False

    record = item.get("post_merge_revalidation", {})
    assert record.get("measured") is False
    assert "budget" in record.get("reason", "")
    assert "baseline_comparison" not in record
    assert runner_shared.revalidation_was_unmeasured(item) is True


def test_case_b_real_red_is_measured(
    repo_fixture: tuple[Path, str, dict[str, Any], dict[str, Any], Path],
) -> None:
    """(b) a real red (budget_only=False, failures=('FAILED tests/t.py::t - x',))
    -> record measured is True and revalidation_was_unmeasured(item) is False.
    """
    repo, _head, state, item, run_dir = repo_fixture
    stub_result = _make_suite_check_result(
        repo,
        passing=False,
        exit_code=1,
        failures=("FAILED tests/t.py::t - x",),
        budget_only=False,
        reason="tests failed",
    )
    runner = runner_shared.make_integration_validation_runner(
        state,
        run_dir,
        item,
        suite_check=lambda _p, _r: stub_result,
    )
    verdict = runner("", ["x"])
    assert verdict is False

    record = item.get("post_merge_revalidation", {})
    assert record.get("measured") is True
    assert runner_shared.revalidation_was_unmeasured(item) is False


def test_case_c_budget_only_with_failures_is_measured(
    repo_fixture: tuple[Path, str, dict[str, Any], dict[str, Any], Path],
) -> None:
    """(c) budget_only=True but failures non-empty -> still measured
    (a real failure is never hidden behind the budget).
    """
    repo, _head, state, item, run_dir = repo_fixture
    stub_result = _make_suite_check_result(
        repo,
        passing=False,
        exit_code=1,
        failures=("FAILED tests/t.py::t - x",),
        budget_only=True,
        reason="tests failed and budget exceeded",
    )
    runner = runner_shared.make_integration_validation_runner(
        state,
        run_dir,
        item,
        suite_check=lambda _p, _r: stub_result,
    )
    verdict = runner("", ["x"])
    assert verdict is False

    record = item.get("post_merge_revalidation", {})
    assert record.get("measured") is True
    assert runner_shared.revalidation_was_unmeasured(item) is False


def test_case_d_remeasured_not_cached(
    repo_fixture: tuple[Path, str, dict[str, Any], dict[str, Any], Path],
) -> None:
    """(d) RE-MEASURED, NOT CACHED: with a stub that returns the budget-only result on its first
    call and a green result (passing=True, exit_code=0) on its second, call a fresh runner twice
    on the same state and tree; assert the stub was called twice, the first call returned False
    with measured is False, the second returned True with the record's passed is True and
    cached is False, and that after the first call state.get(runner_shared.REVALIDATION_CACHE_KEY, {})
    has no entry for the tree.
    """
    repo, _head, state, item, run_dir = repo_fixture
    budget_result = _make_suite_check_result(
        repo,
        passing=False,
        exit_code=1,
        failures=(),
        budget_only=True,
        reason="core tier wall-time budget exceeded",
    )
    green_result = _make_suite_check_result(
        repo,
        passing=True,
        exit_code=0,
        failures=(),
        budget_only=False,
        reason="all tests passed",
    )

    call_count = 0

    def stub(_path: Path, _run_id: str) -> runner_shared.SuiteCheckResult:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return budget_result
        return green_result

    # First run on tree
    runner1 = runner_shared.make_integration_validation_runner(
        state,
        run_dir,
        item,
        suite_check=stub,
    )
    verdict1 = runner1("", ["x"])
    assert verdict1 is False
    assert item["post_merge_revalidation"]["measured"] is False

    tree_id = item["post_merge_revalidation"]["tree"]
    cache = state.get(runner_shared.REVALIDATION_CACHE_KEY, {})
    assert tree_id not in cache

    # Second run on same state and tree with fresh runner
    runner2 = runner_shared.make_integration_validation_runner(
        state,
        run_dir,
        item,
        suite_check=stub,
    )
    verdict2 = runner2("", ["x"])
    assert verdict2 is True
    assert call_count == 2
    assert item["post_merge_revalidation"]["passed"] is True
    assert item["post_merge_revalidation"]["cached"] is False


def test_case_e_routing_defers_as_merge_unchecked(
    repo_fixture: tuple[Path, str, dict[str, Any], dict[str, Any], Path],
) -> None:
    """(e) after case (a), call runner_shared.record_integration_refusal with run_dir,
    the same state and item, attempt={}, branch="b",
    integ_kind=runner_shared.INTEGRATION_REFUSAL_CONFLICT, a reason tagged with the combined-red cause
    token via runner_shared.tag_integration_cause(runner_shared.INTEGRATION_CAUSE_GATE_COMBINED_RED, "..."),
    and recording save_state/append_jsonl stubs, asserting
    item["integration_ladder"]["kind"] == runner_shared.INTEGRATION_REFUSAL_UNMEASURED,
    item["integration_ladder"]["deferrable"] is True, and the returned decision's deferred is True.
    """
    repo, _head, state, item, run_dir = repo_fixture
    stub_result = _make_suite_check_result(
        repo,
        passing=False,
        exit_code=1,
        failures=(),
        budget_only=True,
        reason="core tier wall-time budget exceeded",
    )
    runner = runner_shared.make_integration_validation_runner(
        state,
        run_dir,
        item,
        suite_check=lambda _p, _r: stub_result,
    )
    assert runner("", ["x"]) is False

    saved_states: list[tuple[Path, Any]] = []
    appended_events: list[tuple[Path, Any]] = []

    def fake_save_state(d: Path, s: Any) -> None:
        saved_states.append((d, s))

    def fake_append_jsonl(p: Path, obj: Any) -> None:
        appended_events.append((p, obj))

    tagged_reason = runner_shared.tag_integration_cause(
        runner_shared.INTEGRATION_CAUSE_GATE_COMBINED_RED,
        "suite failed combined revalidation",
    )

    decision = runner_shared.record_integration_refusal(
        run_dir=run_dir,
        state=state,
        item=item,
        attempt={},
        branch="b",
        integ_kind=runner_shared.INTEGRATION_REFUSAL_CONFLICT,
        integ_reason=tagged_reason,
        save_state=fake_save_state,
        append_jsonl=fake_append_jsonl,
    )

    assert (
        item["integration_ladder"]["kind"]
        == runner_shared.INTEGRATION_REFUSAL_UNMEASURED
    )
    assert item["integration_ladder"]["deferrable"] is True
    assert decision.deferred is True


def test_case_f_end_to_end_run_suite_check_budget_only(tmp_path: Path) -> None:
    """(f) end-to-end runner_shared.run_suite_check on a fixture repo whose only test passes
    and whose conftest.py reproduces the enforced budget rule (banner CORE TIER BUDGET EXCEEDED on stderr,
    session.exitstatus = 1 when AW_CORE_BUDGET_ENFORCE=1, AW_TEST_CPU_COUNT>=12, over AW_CORE_BUDGET_SECONDS),
    built with tests.support.init_repo and committed with support.git(..., env=support.clean_git_env()),
    run with AW_CORE_BUDGET_ENFORCE=1, AW_CORE_BUDGET_SECONDS=0.01, AW_TEST_CPU_COUNT=12 patched into os.environ
    via mock.patch.dict AND, inside that patch, PYTEST_XDIST_WORKER, PYTEST_XDIST_WORKER_COUNT,
    PYTEST_ADDOPTS, AW_SUITE_SLOT_HELD and AW_TEST_TIER popped.
    Assert passing is False, exit_code == 1, failures == () and budget_only is True.
    """
    repo = support.init_repo(tmp_path / "e2e_repo")
    tests_dir = repo / "tests"
    tests_dir.mkdir(parents=True, exist_ok=True)
    (tests_dir / "test_sample.py").write_text(
        "import time\n"
        "def test_passing():\n"
        "    time.sleep(0.02)\n"
        "    assert True\n",
        encoding="utf-8",
    )
    conftest_src = (
        "import os\n"
        "import sys\n"
        "import time\n"
        "import pytest\n"
        "\n"
        "_start = 0.0\n"
        "\n"
        "@pytest.hookimpl\n"
        "def pytest_sessionstart(session):\n"
        "    global _start\n"
        "    _start = time.perf_counter()\n"
        "\n"
        "@pytest.hookimpl(trylast=True)\n"
        "def pytest_sessionfinish(session, exitstatus):\n"
        "    if 'PYTEST_XDIST_WORKER' in os.environ:\n"
        "        return\n"
        "    elapsed = time.perf_counter() - _start\n"
        "    budget = float(os.environ.get('AW_CORE_BUDGET_SECONDS', '30.0'))\n"
        "    cpu_count = int(os.environ.get('AW_TEST_CPU_COUNT', '1'))\n"
        "    enforce = os.environ.get('AW_CORE_BUDGET_ENFORCE') == '1'\n"
        "    if enforce and cpu_count >= 12 and elapsed > budget:\n"
        "        sys.stderr.write('CORE TIER BUDGET EXCEEDED\\n')\n"
        "        session.exitstatus = 1\n"
    )
    (repo / "conftest.py").write_text(conftest_src, encoding="utf-8")
    (repo / "pytest.ini").write_text("[pytest]\ntestpaths = tests\n", encoding="utf-8")

    clean_env = support.clean_git_env()
    support.git(repo, "add", "-A", env=clean_env)
    support.git(repo, "commit", "-m", "init", env=clean_env)

    env_overrides = {
        "AW_CORE_BUDGET_ENFORCE": "1",
        "AW_CORE_BUDGET_SECONDS": "0.01",
        "AW_TEST_CPU_COUNT": "12",
        "AW_NO_REEXEC": "1",
    }
    with mock.patch.dict(os.environ, env_overrides, clear=False):
        for k in (
            "PYTEST_XDIST_WORKER",
            "PYTEST_XDIST_WORKER_COUNT",
            "PYTEST_ADDOPTS",
            "AW_SUITE_SLOT_HELD",
            "AW_TEST_TIER",
        ):
            os.environ.pop(k, None)

        res = runner_shared.run_suite_check(repo, "run-o58dro-e2e")

    assert res.passing is False
    assert res.exit_code == 1
    assert res.failures == ()
    assert res.budget_only is True
