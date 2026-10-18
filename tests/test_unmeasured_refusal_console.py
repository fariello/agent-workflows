"""Operator-facing surfaces report the RECORDED refusal reason, not the raw gate reason (plan h8peam).

When post-merge revalidation could not measure the merge result, `record_integration_refusal`
reclassifies the refusal to `merge-unchecked` and records a token-stripped "COULD NOT MEASURE"
reason. These tests drive the real runner paths and assert that the stderr line, the structured
refusal record, and the rung-3 operator question all carry that recorded reason, and never the raw
combined-red gate message or its `[aw-integration-cause=...]` token. A measured red is the control:
it must still report the genuine `integration_failed_combined_red` status.
"""

from __future__ import annotations

import contextlib
import io
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest import mock

from agent_workflows import agy_runipd, oc_runipd, runner_shared
from tests import support
from tests import test_budget_only_combined_red_e2e as _e2e

BOTH = ("oc_runipd", "agy_runipd")
_MODULES = {"oc_runipd": oc_runipd, "agy_runipd": agy_runipd}

# The reclassified prefix `record_integration_refusal` writes. Matched case-sensitively: the
# deferral verdict line already prints lowercase "could not MEASURE" before the fix.
RECLASSIFIED = "COULD NOT MEASURE"
RAW_STATUS = "integration_failed_combined_red"
CAUSE_TOKEN = "[aw-integration-cause="

_GATE_REASON = runner_shared.tag_integration_cause(
    runner_shared.INTEGRATION_CAUSE_GATE_COMBINED_RED,
    "integration gate did not pass (integration_failed_combined_red): "
    "full_revalidation_check[integration]: Full test suite / revalidation failed after "
    "merging isolated lanes (per-lane-green + combined-red).",
)


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True)


def _line(stderr: str, marker: str) -> str:
    hits = [ln for ln in stderr.splitlines() if marker in ln]
    if len(hits) != 1:
        raise AssertionError(
            f"expected one {marker!r} line, got {hits!r} in:\n{stderr}"
        )
    return hits[0]


def _unmeasured_integrate(item: dict[str, Any]) -> tuple[bool, str, str]:
    item[runner_shared.REVALIDATION_CACHE_KEY] = {
        "passed": False,
        "measured": False,
        "reason": "core-tier wall-time budget exceeded: 35.2s > 30.0s",
    }
    return False, _GATE_REASON, runner_shared.INTEGRATION_REFUSAL_CONFLICT


class _Handle:
    def __init__(self, branch: str) -> None:
        self.branch = branch


def _init_repo(td: str) -> Path:
    repo = Path(td) / "repo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "test@example.invalid")
    _git(repo, "config", "user.name", "Test")
    _git(repo, "config", "commit.gpgsign", "false")
    (repo / ".gitignore").write_text(".aw/\n", encoding="utf-8")
    (repo / "base.txt").write_text("base\n", encoding="utf-8")
    _git(repo, "add", ".gitignore", "base.txt")
    _git(repo, "commit", "-qm", "initial")
    return repo


class _ExecuteFixture(_e2e.TestBudgetOnlyCombinedRedE2E):
    """Borrow the shared driver fixture. Never collected: the leading underscore keeps pytest's
    `Test*` class pattern from matching, and `__test__ = False` stops unittest collection too."""

    __test__ = False

    def runTest(self) -> None:  # pragma: no cover - fixture holder only
        pass


class TestUnmeasuredRefusalConsole(unittest.TestCase):
    def setUp(self) -> None:
        support.declare_execution_role(self)
        self._fx = _ExecuteFixture()

    def _drive_execute(
        self,
        runner: str,
        td: str,
        reval: runner_shared.SuiteCheckResult,
        retry_budget: int,
    ) -> tuple[dict[str, Any], str]:
        repo, run_dir, state, item = self._fx._setup_driver_fixture(
            td, retry_budget=retry_budget, integration_retry_limit=10
        )

        def fake_suite_check(
            path: Path, run_id: str = ""
        ) -> runner_shared.SuiteCheckResult:
            if str(path).startswith(str(run_dir / "revalidation")):
                return reval
            return self._fx._passing_suite(repo)

        def fake_launcher(state_arg, rd, itm, *args, **kwargs):
            work_dir = kwargs.get("work_dir")
            target = Path(work_dir) if work_dir else repo
            (target / "clash.txt").write_text("lane line\n", encoding="utf-8")
            _git(target, "add", "clash.txt")
            _git(target, "commit", "-qm", "lane commit")
            (rd / "outcomes" / f"{itm['position']:02d}-{itm['id6']}.json").write_text(
                json.dumps(
                    {
                        "disposition": "executed",
                        "pushed": False,
                        "defect_report": {"state": "none-found", "findings": []},
                    }
                ),
                encoding="utf-8",
            )
            return 0, "ses1", str(rd / "log"), [runner]

        driver = _MODULES[runner]
        launcher = "run_opencode" if runner == "oc_runipd" else "run_agy_turn"
        err = io.StringIO()
        with mock.patch.object(driver, launcher, fake_launcher), mock.patch.object(
            driver, "run_suite_check", fake_suite_check
        ), mock.patch.object(
            runner_shared, "start_suite_baseline", return_value=(None, None)
        ), contextlib.redirect_stderr(err):
            driver.execute_item(run_dir, state, item, recovery=False)
        return item, err.getvalue()

    def test_execute_unmeasured_refusal_reports_reclassified_reason(self) -> None:
        for runner in BOTH:
            with self.subTest(runner=runner), tempfile.TemporaryDirectory() as td:
                reval = runner_shared.SuiteCheckResult(
                    passing=False,
                    exit_code=1,
                    failures=(),
                    summary="745 passed",
                    budget_only=True,
                    reason="core-tier wall-time budget exceeded: 35.2s > 30.0s",
                    cwd=td,
                    timeout_seconds=60.0,
                    elapsed_seconds=35.2,
                )
                item, stderr = self._drive_execute(runner, td, reval, retry_budget=2)
                self.assertEqual(
                    item["integration_ladder"]["kind"],
                    runner_shared.INTEGRATION_REFUSAL_UNMEASURED,
                )
                line = _line(stderr, "NOT integrated to main")
                self.assertIn(RECLASSIFIED, line)
                self.assertNotIn(RAW_STATUS, line)
                self.assertNotIn(CAUSE_TOKEN, line)
                refusal_reason = item["refusal"]["reason"]
                self.assertIn(RECLASSIFIED, refusal_reason)
                self.assertNotIn(RAW_STATUS, refusal_reason)
                self.assertNotIn("it was RED", refusal_reason)

    def test_execute_measured_red_still_reports_genuine_gate_status(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            reval = runner_shared.SuiteCheckResult(
                passing=False,
                exit_code=1,
                failures=("FAILED tests/test_foo.py::test_failing_case - boom",),
                summary="1 failed, 744 passed",
                budget_only=False,
                reason="1 test failed",
                cwd=td,
                timeout_seconds=60.0,
                elapsed_seconds=5.0,
            )
            item, stderr = self._drive_execute("oc_runipd", td, reval, retry_budget=0)
            self.assertNotEqual(
                item["integration_ladder"]["kind"],
                runner_shared.INTEGRATION_REFUSAL_UNMEASURED,
            )
            self.assertIn(RAW_STATUS, item["refusal"]["reason"])
            line = _line(stderr, "NOT integrated to main")
            self.assertIn(RAW_STATUS, line)
            self.assertNotIn(RECLASSIFIED, line)
            self.assertNotIn(CAUSE_TOKEN, line)

    def test_retired_lane_unmeasured_refusal_reports_reclassified_reason(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _init_repo(td)
            run_dir = repo / ".aw" / "records" / "runs" / "run-test"
            run_dir.mkdir(parents=True)
            item: dict[str, Any] = {
                "id6": "ret001",
                "setid": "demo",
                "status": "running",
            }
            state: dict[str, Any] = {
                "run_id": "run-test",
                "queue": [item],
                "options": {},
            }

            def integrate_lane_branch(_repo, _handle, _id6, _runner):
                return _unmeasured_integrate(item)

            err = io.StringIO()
            with contextlib.redirect_stderr(err):
                disposition = runner_shared.integrate_retired_lane(
                    repo=repo,
                    run_dir=run_dir,
                    state=state,
                    item=item,
                    attempt={},
                    wt_handle=_Handle("aw/lane/ret001"),
                    work_dir=None,
                    host_labels=runner_shared.OC_HOST_LABELS,
                    save_state=lambda *a, **k: None,
                    append_jsonl=lambda *a, **k: None,
                    integrate_lane_branch=integrate_lane_branch,
                    make_validation_runner=lambda *a, **k: None,
                    run_suite_check=lambda *a, **k: None,
                    process_backlog_close=lambda *a, **k: None,
                    git_head=lambda _p: "",
                    git_status=lambda _p: "",
                )
            self.assertEqual(disposition, runner_shared.INTEGRATION_DEFERRED_STATUS)
            line = _line(err.getvalue(), "NOT integrated to main")
            self.assertIn("retired on lane", line)
            self.assertIn(RECLASSIFIED, line)
            self.assertNotIn(RAW_STATUS, line)
            self.assertNotIn(CAUSE_TOKEN, line)

    def test_deferred_reattempt_operator_question_reports_reclassified_reason(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _init_repo(td)
            run_dir = repo / ".aw" / "records" / "runs" / "run-test"
            run_dir.mkdir(parents=True)
            item: dict[str, Any] = {
                "id6": "abc123",
                "setid": "demo",
                "action": "execute",
                "status": runner_shared.INTEGRATION_DEFERRED_STATUS,
                "integration_attempts": 1,
                "attempts": [{}],
            }
            state: dict[str, Any] = {
                "run_id": "run-test",
                "queue": [item],
                "options": {
                    "integration_retry_limit": 0,
                    "on_integration_blocked": "defer",
                },
            }
            questions: list[str] = []

            def fake_prompt(question: str, *args: Any, **kwargs: Any) -> None:
                questions.append(question)
                return None

            err = io.StringIO()
            with mock.patch.object(
                runner_shared, "prompt_for_gate_phrase", fake_prompt
            ), contextlib.redirect_stderr(err), contextlib.redirect_stdout(
                io.StringIO()
            ):
                runner_shared.reattempt_deferred_integrations(
                    repo=repo,
                    run_dir=run_dir,
                    state=state,
                    integrate=lambda itm, _h: _unmeasured_integrate(itm),
                    finish_integrated=lambda *a, **k: None,
                    save_state=lambda *a, **k: None,
                    append_jsonl=lambda *a, **k: None,
                    handle_for=lambda _itm: _Handle("aw/lane/abc123"),
                    ask=True,
                    interactive=True,
                )
            self.assertEqual(len(questions), 1, questions)
            self.assertIn("lane abc123 cannot integrate:", questions[0])
            self.assertIn(RECLASSIFIED, questions[0])
            self.assertNotIn(RAW_STATUS, questions[0])
            self.assertNotIn(CAUSE_TOKEN, questions[0])


if __name__ == "__main__":
    unittest.main()
