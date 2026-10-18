"""Behavioral tests proving runner revalidation seams report all-green over-budget trees as green.

Backlog m8d13e / IPD t54fet (Task groups 1 & 2):
Proves the three runner seams that produce integration decisions:
1. runner_shared.run_suite_check (the integration gate check)
2. runner_shared.start_suite_baseline (the concurrent pre-work baseline)
3. runner_shared.make_integration_validation_runner (post-merge revalidation)

Each seam is driven against an over-budget git fixture repository whose only test
passes but always overruns a tiny core-tier budget. Under default (unset) enforcement
each seam reports green. Under explicit AW_CORE_BUDGET_ENFORCE=1, each seam trips
the budget and reports red with zero failing test IDs (the positive control).
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from unittest import mock


from agent_workflows import runner_shared

REPO_ROOT = Path(__file__).resolve().parent.parent

FIXTURE_CONFTEST = """\
import os
import sys
import time
import pytest

@pytest.hookimpl
def pytest_sessionstart(session):
    session.config._fixture_start_time = time.perf_counter()

@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session, exitstatus):
    if "PYTEST_XDIST_WORKER" in os.environ:
        return
    start_time = getattr(session.config, "_fixture_start_time", None)
    if start_time is None:
        return
    elapsed = time.perf_counter() - start_time
    budget_env = os.environ.get("AW_CORE_BUDGET_SECONDS")
    budget = float(budget_env) if budget_env else 30.0
    if elapsed > budget:
        raw_cpu = os.environ.get("AW_TEST_CPU_COUNT")
        cpu_count = int(raw_cpu if raw_cpu else (os.cpu_count() or 1))
        enforce = os.environ.get("AW_CORE_BUDGET_ENFORCE") != "0"
        msg = (
            "\\n================================ CORE TIER BUDGET EXCEEDED ================================\\n"
            f"Core tier wall time: {elapsed:.2f}s exceeded budget of {budget:.2f}s.\\n"
            "===========================================================================================\\n"
        )
        if cpu_count >= 12 and enforce:
            sys.stderr.write(msg)
            session.exitstatus = 1
        else:
            sys.stderr.write(f"\\nWARNING: {msg}")
"""


def _fixture_env(extra: dict[str, str] | None = None) -> dict[str, str]:
    """Return environment with isolation defaults and budget configuration."""
    env = dict(os.environ)
    env["AW_NO_REEXEC"] = "1"
    env["PYTHONPATH"] = str(REPO_ROOT)
    env["AW_CORE_BUDGET_SECONDS"] = "0.01"
    env["AW_TEST_CPU_COUNT"] = "12"
    for key in (
        "PYTEST_ADDOPTS",
        "PYTEST_CURRENT_TEST",
        "PYTEST_XDIST_WORKER",
        "AW_TEST_TIER",
        "AW_CORE_BUDGET_ENFORCE",
        "AW_SUITE_SLOT_HELD",
    ):
        env.pop(key, None)
    if extra:
        env.update(extra)
    return env


def _over_budget_repo(path: Path) -> Path:
    """Initialize a git repository with an over-budget conftest and one passing test."""
    from tests.repo_template import copy_template_repo

    copy_template_repo(path)
    (path / ".gitignore").write_text(".pytest_cache/\n__pycache__/\n", encoding="utf-8")
    (path / "pytest.ini").write_text(
        "[pytest]\naddopts = -q\ntestpaths = tests\n", encoding="utf-8"
    )
    tests_dir = path / "tests"
    tests_dir.mkdir(parents=True, exist_ok=True)
    (tests_dir / "test_ok.py").write_text(
        "import time\n\n" "def test_ok():\n" "    time.sleep(0.05)\n",
        encoding="utf-8",
    )
    (path / "conftest.py").write_text(FIXTURE_CONFTEST, encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=path, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-qm", "initial fixture"],
        cwd=path,
        check=True,
        capture_output=True,
    )
    return path


# ---------------------------------------------------------------------------
# Seam 1: runner_shared.run_suite_check (E-02)
# ---------------------------------------------------------------------------


def test_run_suite_check_green_on_all_green_over_budget_tree(tmp_path: Path) -> None:
    """Seam 1 reports passing=True on an all-green over-budget tree under default demotion."""
    repo = _over_budget_repo(tmp_path / "seam1_green")
    with mock.patch.dict(os.environ, _fixture_env(), clear=True):
        res = runner_shared.run_suite_check(repo, "run-m8d13e01")
        assert res.passing is True
        assert res.exit_code == 0
        assert res.cached is False
        assert "AW_CORE_BUDGET_ENFORCE" not in os.environ


def test_run_suite_check_red_when_enforce_requested(tmp_path: Path) -> None:
    """Seam 1 positive control: AW_CORE_BUDGET_ENFORCE=1 trips the budget with failures=()."""
    repo = _over_budget_repo(tmp_path / "seam1_red")
    with mock.patch.dict(
        os.environ, _fixture_env({"AW_CORE_BUDGET_ENFORCE": "1"}), clear=True
    ):
        res = runner_shared.run_suite_check(repo, "run-m8d13e01_red")
        assert res.passing is False
        assert res.exit_code == 1
        assert res.failures == ()


# ---------------------------------------------------------------------------
# Seam 2: runner_shared.start_suite_baseline (E-03)
# ---------------------------------------------------------------------------


def test_suite_baseline_green_on_all_green_over_budget_tree(tmp_path: Path) -> None:
    """Seam 2 reports completed with exit_code=0 on an all-green over-budget tree."""
    repo = _over_budget_repo(tmp_path / "seam2_green")
    head = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()

    with mock.patch.dict(os.environ, _fixture_env(), clear=True):
        run_obj, absent_obj = runner_shared.start_suite_baseline(
            repo,
            id6="m8d13e",
            attempt=1,
            base_commit=head,
            argv=list(runner_shared.SUITE_CHECK_ARGV),
            extract_failures=runner_shared.extract_suite_failures,
            parse_summary=runner_shared.parse_suite_summary,
        )
        assert absent_obj is None
        assert run_obj is not None
        try:
            baseline = run_obj.collect(wait_seconds=120.0)
        finally:
            runner_shared.remove_suite_baseline_checkout(repo, run_obj.checkout)

        assert baseline.state == runner_shared.SUITE_BASELINE_COMPLETED
        assert baseline.exit_code == 0
        assert baseline.failures == ()


def test_suite_baseline_red_when_enforce_requested(tmp_path: Path) -> None:
    """Seam 2 positive control: AW_CORE_BUDGET_ENFORCE=1 reports exit_code != 0 with failures=()."""
    repo = _over_budget_repo(tmp_path / "seam2_red")
    head = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()

    with mock.patch.dict(
        os.environ, _fixture_env({"AW_CORE_BUDGET_ENFORCE": "1"}), clear=True
    ):
        run_obj, absent_obj = runner_shared.start_suite_baseline(
            repo,
            id6="m8d13e",
            attempt=1,
            base_commit=head,
            argv=list(runner_shared.SUITE_CHECK_ARGV),
            extract_failures=runner_shared.extract_suite_failures,
            parse_summary=runner_shared.parse_suite_summary,
        )
        assert absent_obj is None
        assert run_obj is not None
        try:
            baseline = run_obj.collect(wait_seconds=120.0)
        finally:
            runner_shared.remove_suite_baseline_checkout(repo, run_obj.checkout)

        assert baseline.exit_code != 0
        assert baseline.failures == ()


# ---------------------------------------------------------------------------
# Seam 3: runner_shared.make_integration_validation_runner (E-04)
# ---------------------------------------------------------------------------


def test_post_merge_revalidation_green_on_all_green_over_budget_tree(
    tmp_path: Path,
) -> None:
    """Seam 3 returns True and records passed=True on an all-green over-budget tree."""
    repo = _over_budget_repo(tmp_path / "seam3_green")
    head = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    run_dir = tmp_path / "run_dir_green"
    run_dir.mkdir(parents=True, exist_ok=True)
    state: dict[str, object] = {
        "repo": str(repo),
        "run_id": "run-m8d13e03",
        "options": {"validate": False},
    }
    item: dict[str, object] = {
        "id6": "m8d13e",
        "base_commit": head,
        "lane_head": head,
        "attempts": [],
    }

    with mock.patch.dict(os.environ, _fixture_env(), clear=True):
        reval_runner = runner_shared.make_integration_validation_runner(
            state,
            run_dir,
            item,
            suite_check=runner_shared.run_suite_check,
        )
        assert reval_runner("", ["tests/test_ok.py"]) is True
        reval_rec = item.get("post_merge_revalidation", {})
        assert isinstance(reval_rec, dict)
        assert reval_rec.get("passed") is True


def test_post_merge_revalidation_red_when_enforce_requested(tmp_path: Path) -> None:
    """Seam 3 positive control: AW_CORE_BUDGET_ENFORCE=1 returns False, passed=False, failures=[]."""
    repo = _over_budget_repo(tmp_path / "seam3_red")
    head = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    run_dir = tmp_path / "run_dir_red"
    run_dir.mkdir(parents=True, exist_ok=True)
    state: dict[str, object] = {
        "repo": str(repo),
        "run_id": "run-m8d13e03_red",
        "options": {"validate": False},
    }
    item: dict[str, object] = {
        "id6": "m8d13e",
        "base_commit": head,
        "lane_head": head,
        "attempts": [],
    }

    with mock.patch.dict(
        os.environ, _fixture_env({"AW_CORE_BUDGET_ENFORCE": "1"}), clear=True
    ):
        reval_runner = runner_shared.make_integration_validation_runner(
            state,
            run_dir,
            item,
            suite_check=runner_shared.run_suite_check,
        )
        assert reval_runner("", ["tests/test_ok.py"]) is False
        reval_rec = item.get("post_merge_revalidation", {})
        assert isinstance(reval_rec, dict)
        assert reval_rec.get("passed") is False
        assert list(reval_rec.get("failures", [])) == []
