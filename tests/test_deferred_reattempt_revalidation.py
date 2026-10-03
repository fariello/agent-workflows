"""Tests for deferred re-attempt post-merge revalidation.

Plan vfcnyd (devalrun):
- Asserts that deferred integration retry revalidates on both hosts
- Asserts the revalidation suite runs against a materialized merge result
- Asserts that revalidation results are recorded on the live queue item
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest import mock

from agent_workflows import agy_runipd, oc_runipd, runner_shared


def _git(cwd: Path, args: list[str]) -> tuple[int, str, str]:
    proc = subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.returncode, proc.stdout, proc.stderr


class _SuiteResultStub:
    """Attribute-carrying suite check result stub.

    Per PR-102 / F-11, make_integration_validation_runner reads four attributes
    off the result object via getattr (passing, reason, failures, exit_code),
    so a tuple-returning stub fails silently.
    """

    def __init__(
        self,
        passing: bool = True,
        reason: str = "suite passed",
        failures: tuple[str, ...] = (),
        exit_code: int = 0,
    ) -> None:
        self.passing = passing
        self.reason = reason
        self.failures = failures
        self.exit_code = exit_code


class DeferredReattemptRevalidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = Path(tempfile.mkdtemp(prefix="test-devalrun-"))
        self.repo = self._tmp / "repo"
        self.repo.mkdir()
        self.run_dir = self._tmp / "run"
        self.run_dir.mkdir()
        self.lane_worktree = self._tmp / "lane_wt"

        _git(self.repo, ["init", "-b", "main"])
        _git(self.repo, ["config", "user.name", "Test Runner"])
        _git(self.repo, ["config", "user.email", "runner@example.invalid"])

        readme = self.repo / "README.md"
        readme.write_text("# Test Repo\n", encoding="utf-8")
        _git(self.repo, ["add", "README.md"])
        _git(self.repo, ["commit", "-m", "initial commit"])

        rc, out, _ = _git(self.repo, ["rev-parse", "HEAD"])
        self.assertEqual(rc, 0)
        self.base_commit = out.strip()

        _git(self.repo, ["checkout", "-b", "aw/lane/dr0001"])
        work_file = self.repo / "work.txt"
        work_file.write_text("lane work\n", encoding="utf-8")
        _git(self.repo, ["add", "work.txt"])
        _git(self.repo, ["commit", "-m", "lane commit"])
        _git(self.repo, ["checkout", "main"])

    def tearDown(self) -> None:
        shutil.rmtree(self._tmp, ignore_errors=True)

    def _state_and_item(self, host_label: str) -> tuple[dict[str, Any], dict[str, Any]]:
        item = {
            "position": 1,
            "id6": "dr0001",
            "setid": "dr",
            "status": runner_shared.INTEGRATION_DEFERRED_STATUS,
            "action": "execute",
            "file": "x.ipd.md",
            "configured_file": "x.ipd.md",
            "preserved_branch": "aw/lane/dr0001",
            "preserved_base": self.base_commit,
            "preserved_worktree": str(self.lane_worktree),
            "preserved_lane_id": "dr0001",
            "attempts": [
                {
                    "worktree_base": self.base_commit,
                    "worktree_branch": "aw/lane/dr0001",
                }
            ],
        }
        state = {
            "run_id": "run-test",
            "host": host_label,
            "repo": str(self.repo),
            "queue": [item],
            "selectors": ["dr0001"],
            "created_at": "2026-09-25T00:00:00+00:00",
            "updated_at": "2026-09-25T00:00:00+00:00",
            "set_sessions": {},
            "options": {
                "validate": False,
                "integration_retry_limit": 10,
                "on_integration_blocked": "defer",
            },
        }
        return state, item

    def _run_retry_revalidation_test(self, host: Any, host_label: str) -> None:
        state, item = self._state_and_item(host_label)

        # Confirm resolved endpoints meet the three resolvability requirements:
        # base and branch are non-empty; head is resolved from the branch by git rev-parse.
        base, branch, head = runner_shared.resolve_lane_endpoints(item)
        self.assertEqual(base, self.base_commit)
        self.assertEqual(branch, "aw/lane/dr0001")
        self.assertEqual(head, "")

        suite_calls: list[tuple[Path, str]] = []

        def fake_suite_check(path: Path, run_id: str) -> _SuiteResultStub:
            suite_calls.append((path, run_id))
            return _SuiteResultStub(
                passing=True,
                reason="suite passed",
                failures=(),
                exit_code=0,
            )

        def fake_integrate(
            repo_path: Any, handle: Any, item_id6: str, runner: Any
        ) -> tuple[bool, str, str]:
            ok = runner("", []) if callable(runner) else False
            return (
                ok,
                "integrated" if ok else "gate refused",
                "clean" if ok else runner_shared.INTEGRATION_REFUSAL_CONFLICT,
            )

        with (
            mock.patch.object(
                host, "integrate_lane_branch", side_effect=fake_integrate
            ),
            mock.patch.object(host, "run_suite_check", side_effect=fake_suite_check),
        ):
            host.retry_deferred_integrations(self.run_dir, state)

        # Assertion (a): stub suite checker was invoked exactly once
        self.assertEqual(len(suite_calls), 1)

        # Assertion (b): checker invoked against a materialized merge result directory
        # under <run_dir>/revalidation/, not against primary checkout or lane worktree
        called_path, run_id_arg = suite_calls[0]
        self.assertEqual(run_id_arg, "run-test")
        reval_dir = self.run_dir / "revalidation"
        self.assertTrue(
            str(called_path).startswith(str(reval_dir)),
            f"Expected {called_path} to be under {reval_dir}",
        )
        self.assertNotEqual(called_path, self.repo)
        self.assertNotEqual(called_path, self.lane_worktree)

        # Assertion (c): post_merge_revalidation record present on the LIVE queue item
        self.assertIn(runner_shared.REVALIDATION_CACHE_KEY, item)
        self.assertTrue(item[runner_shared.REVALIDATION_CACHE_KEY].get("passed"))
        self.assertTrue(item[runner_shared.REVALIDATION_CACHE_KEY].get("measured"))

    def test_oc_deferred_reattempt_revalidation(self) -> None:
        self._run_retry_revalidation_test(oc_runipd, "oc")

    def test_agy_deferred_reattempt_revalidation(self) -> None:
        self._run_retry_revalidation_test(agy_runipd, "agy")
