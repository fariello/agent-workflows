"""Tests for fork residue deduplication and shared runner shells.

Plan 184tn9 (forkresid):
- Behavioral test for deferred retry post-merge unmeasured reclassification
- Behavioral test for lane reclaim prompt suppression and TTY gating
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


class _TTYStub:
    def __init__(self, readline_value: str = "") -> None:
        self._readline_value = readline_value
        self.buffer = ""

    def isatty(self) -> bool:
        return True

    def readline(self) -> str:
        return self._readline_value

    def write(self, text: str) -> int:
        self.buffer += text
        return len(text)

    def flush(self) -> None:
        pass


class _NonTTYStub:
    def isatty(self) -> bool:
        return False

    def readline(self) -> str:
        return ""

    def write(self, text: str) -> int:
        return len(text)

    def flush(self) -> None:
        pass


class DeferredRetryUnmeasuredTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = Path(tempfile.mkdtemp(prefix="test-forkresid-"))
        self.repo = self._tmp / "repo"
        self.repo.mkdir()
        self.run_dir = self._tmp / "run"
        self.run_dir.mkdir()

        _git(self.repo, ["init", "-b", "main"])
        _git(self.repo, ["config", "user.name", "Test Runner"])
        _git(self.repo, ["config", "user.email", "runner@example.invalid"])

        readme = self.repo / "README.md"
        readme.write_text("# Test Repo\n", encoding="utf-8")
        _git(self.repo, ["add", "README.md"])
        _git(self.repo, ["commit", "-m", "initial commit"])

        rc, _, _ = _git(self.repo, ["branch", "aw/lane/fr0001"])
        self.assertEqual(rc, 0)

    def tearDown(self) -> None:
        shutil.rmtree(self._tmp, ignore_errors=True)

    def _state_and_item(self, host_label: str) -> tuple[dict[str, Any], dict[str, Any]]:
        item = {
            "position": 1,
            "id6": "fr0001",
            "setid": "fr",
            "status": runner_shared.INTEGRATION_DEFERRED_STATUS,
            "action": "execute",
            "file": "x.ipd.md",
            "configured_file": "x.ipd.md",
            "preserved_branch": "aw/lane/fr0001",
            "preserved_worktree": "",
            "attempts": [{}],
        }
        state = {
            "run_id": "run-test",
            "host": host_label,
            "repo": str(self.repo),
            "queue": [item],
            "selectors": ["fr0001"],
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

    def _run_retry_test(self, host: Any, host_label: str) -> None:
        state, item = self._state_and_item(host_label)

        def fake_integrate(
            repo_path: Any, handle: Any, item_id6: str, runner: Any
        ) -> tuple[bool, str, str]:
            ok = runner("", [])
            return (ok, "gate refused", runner_shared.INTEGRATION_REFUSAL_CONFLICT)

        with mock.patch.object(
            host, "integrate_lane_branch", side_effect=fake_integrate
        ):
            host.retry_deferred_integrations(self.run_dir, state)

        self.assertEqual(
            item["integration_ladder"]["kind"],
            runner_shared.INTEGRATION_REFUSAL_UNMEASURED,
        )
        self.assertTrue(runner_shared.revalidation_was_unmeasured(item))

    def test_oc_deferred_retry_unmeasured(self) -> None:
        self._run_retry_test(oc_runipd, "oc")

    def test_agy_deferred_retry_unmeasured(self) -> None:
        self._run_retry_test(agy_runipd, "agy")


class LanePromptSuppressionTests(unittest.TestCase):
    def _run_lane_prompt_checks(self, host: Any) -> None:
        lane = {"holds_work": True, "lane_id": "x", "branch": "b"}

        # 1. TTY stubs, readline returns "d\n", select ready -> returns "discard"
        stdin_tty = _TTYStub("d\n")
        stderr_tty = _TTYStub()
        with (
            mock.patch("sys.stdin", stdin_tty),
            mock.patch("sys.stderr", stderr_tty),
            mock.patch("select.select", return_value=([stdin_tty], [], [])),
            mock.patch.object(host, "_LANE_PROMPT_DISABLED", False),
        ):
            res = host._lane_reclaim_prompt(lane, "keep")
            self.assertEqual(res, "discard")

        # 2. after disable_lane_prompt() -> returns None
        with mock.patch.object(host, "_LANE_PROMPT_DISABLED", False):
            host.disable_lane_prompt()
            res = host._lane_reclaim_prompt(lane, "keep")
            self.assertIsNone(res)

        # 3. non-TTY stdin -> returns None
        stdin_nontty = _NonTTYStub()
        with (
            mock.patch("sys.stdin", stdin_nontty),
            mock.patch("sys.stderr", stderr_tty),
            mock.patch.object(host, "_LANE_PROMPT_DISABLED", False),
        ):
            res = host._lane_reclaim_prompt(lane, "keep")
            self.assertIsNone(res)

    def test_oc_lane_prompt_suppression(self) -> None:
        self._run_lane_prompt_checks(oc_runipd)

    def test_agy_lane_prompt_suppression(self) -> None:
        self._run_lane_prompt_checks(agy_runipd)
