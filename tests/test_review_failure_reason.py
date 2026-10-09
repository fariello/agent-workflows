# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests for naming the real reason a review turn failed (IPD ckxypc E-01..E-04)."""

from __future__ import annotations

import io
import json
import pathlib
import subprocess
import tempfile
import unittest
from typing import Any, NamedTuple
from unittest import mock

from agent_workflows import (
    lane_containment,
    oc_runipd,
    orchestrator_readiness,
    render_stream,
    runner_shared,
)
from agent_workflows.render_stream import Palette


class HostErrorHelpersUnitTests(unittest.TestCase):
    """Unit tests for E-02 pure helpers in render_stream."""

    def test_host_error_of_event_opencode(self) -> None:
        ev = {
            "type": "error",
            "error": {
                "name": "ContentFilterError",
                "data": {
                    "message": "The response was blocked by the provider's content filter"
                },
            },
        }
        res = render_stream.host_error_of_event(ev)
        self.assertEqual(
            (
                "ContentFilterError",
                "The response was blocked by the provider's content filter",
            ),
            res,
        )

    def test_host_error_of_event_opencode_string_data(self) -> None:
        ev = {
            "type": "error",
            "error": {
                "name": "UnknownError",
                "data": "Operation timed out",
            },
        }
        res = render_stream.host_error_of_event(ev)
        self.assertEqual(("UnknownError", "Operation timed out"), res)

    def test_host_error_of_event_opencode_message_field(self) -> None:
        ev = {
            "type": "error",
            "error": {
                "name": "FallbackError",
                "message": "Fallback message",
            },
        }
        res = render_stream.host_error_of_event(ev)
        self.assertEqual(("FallbackError", "Fallback message"), res)

    def test_host_error_of_event_agy_failed_result(self) -> None:
        ev = {
            "event": "result",
            "result": {
                "status": "ERROR",
                "error": "Antigravity model execution failed",
            },
        }
        res = render_stream.host_error_of_event(ev)
        self.assertEqual(("ERROR", "Antigravity model execution failed"), res)

    def test_host_error_of_event_agy_success_result(self) -> None:
        ev = {
            "event": "result",
            "result": {
                "status": "SUCCESS",
            },
        }
        res = render_stream.host_error_of_event(ev)
        self.assertIsNone(res)

    def test_host_error_of_event_clean_event(self) -> None:
        ev = {"type": "text", "part": {"text": "thinking..."}}
        self.assertIsNone(render_stream.host_error_of_event(ev))

    def test_host_error_of_event_non_dict(self) -> None:
        self.assertIsNone(render_stream.host_error_of_event("not a dict"))
        self.assertIsNone(render_stream.host_error_of_event(None))

    def test_host_error_of_event_bounded(self) -> None:
        long_name = "E" * 200
        long_msg = "M" * 2000
        ev = {
            "type": "error",
            "error": {
                "name": long_name,
                "data": {"message": long_msg},
            },
        }
        res = render_stream.host_error_of_event(ev)
        self.assertIsNotNone(res)
        name, msg = res  # type: ignore[misc]
        self.assertLessEqual(len(name), 80)
        self.assertLessEqual(len(msg), 300)
        self.assertTrue(name.endswith("…"))
        self.assertTrue(msg.endswith("…"))

    def test_scan_last_host_error_fixture(self) -> None:
        fixture_path = (
            pathlib.Path(__file__).parent
            / "fixtures"
            / "session_content_filter_error.jsonl"
        )
        res = render_stream.scan_last_host_error(fixture_path)
        self.assertEqual(
            (
                "ContentFilterError",
                "The response was blocked by the provider's content filter",
            ),
            res,
        )

    def test_scan_last_host_error_clean_log(self) -> None:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8") as tf:
            tf.write(
                '{"type":"text","part":{"text":"hello"}}\n{"type":"step_finish"}\n'
            )
            tf.flush()
            self.assertIsNone(render_stream.scan_last_host_error(tf.name))

    def test_scan_last_host_error_agy_success(self) -> None:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8") as tf:
            tf.write(
                '{"event":"init"}\n{"event":"result","result":{"status":"SUCCESS"}}\n'
            )
            tf.flush()
            self.assertIsNone(render_stream.scan_last_host_error(tf.name))

    def test_scan_last_host_error_agy_failed(self) -> None:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8") as tf:
            tf.write(
                '{"event":"init"}\n'
                '{"event":"result","result":{"status":"FAILED","error":"crash"}}\n'
            )
            tf.flush()
            self.assertEqual(
                ("FAILED", "crash"), render_stream.scan_last_host_error(tf.name)
            )

    def test_scan_last_host_error_missing_path(self) -> None:
        self.assertIsNone(
            render_stream.scan_last_host_error("/nonexistent/file/path.jsonl")
        )

    def test_render_event_error_unchanged(self) -> None:
        ev = {
            "type": "error",
            "error": {
                "name": "ContentFilterError",
                "data": {
                    "message": "The response was blocked by the provider's content filter"
                },
            },
        }
        line = render_stream.render_event(
            json.dumps(ev),
            Palette(False),
            use_unicode=False,
        )
        self.assertEqual(
            "! diag:  ContentFilterError: The response was blocked by the provider's content filter",
            line,
        )

    def test_render_run_summary_table_host_error_own_bullet(self) -> None:
        state = {
            "run_id": "test_run",
            "queue": [
                {
                    "id6": "err001",
                    "status": "fail-gate",
                    "position": 1,
                    "host_error": {"name": "TestError", "message": "A test failure"},
                }
            ],
        }
        summary = render_stream.render_run_summary_table(state, "test")
        self.assertIn("• err001: fail-gate (host TestError: A test failure)", summary)

    def test_render_run_summary_table_host_error_under_bullet(self) -> None:
        from agent_workflows.render_stream import record_refusal

        item = {
            "id6": "err002",
            "status": "fail-gate",
            "position": 1,
            "host_error": {"name": "TestError", "message": "A test failure"},
        }
        record_refusal(
            item, code="some-code", reason="reason text", remedy="remedy text"
        )
        state = {
            "run_id": "test_run",
            "queue": [item],
        }
        summary = render_stream.render_run_summary_table(state, "test")
        self.assertIn("• err002: fail-gate (reason text)", summary)
        self.assertIn("    host error: TestError: A test failure", summary)
        self.assertIn("    → remedy: remedy text", summary)

    def test_write_report_byte_identical_when_no_host_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            run_dir = pathlib.Path(temp)
            state = {
                "run_id": "clean_run",
                "repo": "/tmp/repo",
                "created_at": "2026-10-09T00:00:00Z",
                "updated_at": "2026-10-09T00:00:00Z",
                "selectors": [],
                "queue": [
                    {
                        "id6": "ok0001",
                        "setid": "set1",
                        "position": 1,
                        "action": "review",
                        "status": "reviewed",
                        "attempts": [],
                    }
                ],
            }
            runner_shared.write_report(
                run_dir, state, labels=runner_shared.OC_HOST_LABELS
            )
            report_lines = (
                (run_dir / "execution-report.md")
                .read_text(encoding="utf-8")
                .splitlines()
            )
            self.assertFalse(any("Host errors" in line for line in report_lines))
            self.assertFalse(any("host error" in line.lower() for line in report_lines))


class ReviewFailureReasonIntegrationTests(unittest.TestCase):
    """Integration tests driving execute_item with fake_opencode (cases a, b, c, d)."""

    def _setup_repo_and_plan(
        self,
        tmp: pathlib.Path,
        *,
        id6: str,
        kind: str,
        status: str = "to-review",
    ) -> tuple[pathlib.Path, pathlib.Path, pathlib.Path]:
        repo = tmp / "repo"
        repo.mkdir()
        for cmd in (
            ["git", "init", "-q"],
            ["git", "config", "user.email", "test@example.invalid"],
            ["git", "config", "user.name", "Test"],
        ):
            subprocess.run(cmd, cwd=repo, check=True)
        (repo / ".gitignore").write_text(
            ".aw/records/runs/\n.aw/state/\n", encoding="utf-8"
        )
        plans_dir = repo / ".aw" / "records" / "plans" / "pending"
        plans_dir.mkdir(parents=True)
        plan_name = f"20261007-set1-01-{id6}-test.ipd.md"
        plan_file = plans_dir / plan_name
        plan_file.write_text(
            f"# IPD: Test\n\n"
            f"- Id: {id6}\n"
            f"- Kind: {kind}\n"
            f"- Set: set1\n"
            f"- Order: 1\n"
            f"- Status: {status}\n",
            encoding="utf-8",
        )
        subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
        subprocess.run(["git", "commit", "-qm", "initial"], cwd=repo, check=True)

        run_dir = tmp / "run_dir"
        run_dir.mkdir()
        (run_dir / "outcomes").mkdir()
        (run_dir / "sessions").mkdir()
        (run_dir / "prompts").mkdir()

        return repo, plan_file, run_dir

    def _run_fake_review(
        self,
        *,
        repo: pathlib.Path,
        run_dir: pathlib.Path,
        id6: str,
        fake_script_content: str,
        readiness_ready: bool = True,
        extra_options: dict[str, Any] | None = None,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        fake_bin = run_dir / "fake_opencode"
        fake_bin.write_text(fake_script_content, encoding="utf-8")
        fake_bin.chmod(0o755)

        item = {
            "id6": id6,
            "action": "review",
            "setid": "set1",
            "position": 1,
            "status": "queued",
            "attempts": [],
        }
        opts = {"auto": True, "no_audit": True, "opencode": str(fake_bin)}
        if extra_options:
            opts.update(extra_options)
        state = {
            "run_id": "test_run",
            "repo": str(repo),
            "options": opts,
            "queue": [item],
        }

        class _MockFinding(NamedTuple):
            subject: str
            detail: str
            code: str = "finding-code"
            remedy: str = "fix it"

        readiness_obj = mock.Mock()
        readiness_obj.ready = readiness_ready
        readiness_obj.findings = (
            [_MockFinding("sub", "det", "finding-code", "fix it")]
            if not readiness_ready
            else []
        )

        with (
            mock.patch.object(oc_runipd, "driver_begin", lambda *a, **k: (0, "ok")),
            mock.patch.object(oc_runipd, "driver_finalize", lambda *a, **k: (0, "ok")),
            mock.patch.object(
                oc_runipd, "assert_child_tool_identity", lambda *a, **k: None
            ),
            mock.patch.object(
                orchestrator_readiness,
                "review_readiness",
                lambda *a, **k: readiness_obj,
            ),
            mock.patch("sys.stderr", new_callable=io.StringIO),
        ):
            oc_runipd.execute_item(run_dir, state, item, recovery=False)

        return item, state

    def test_case_a_child_review_content_filter_error(self) -> None:
        """Case (a): emits a content-filter error and exits 1 on a child review."""
        with tempfile.TemporaryDirectory() as temp:
            tmp = pathlib.Path(temp)
            repo, _plan_file, run_dir = self._setup_repo_and_plan(
                tmp, id6="chd001", kind="child"
            )

            script = (
                "#!/usr/bin/env python3\n"
                "import json, sys\n"
                "print(json.dumps({'type':'step_finish','reason':'content-filter'}))\n"
                "print(json.dumps({'type':'error','error':{'name':'ContentFilterError','data':{'message':'The response was blocked by the provider\\'s content filter'}}}))\n"
                "sys.exit(1)\n"
            )
            item, state = self._run_fake_review(
                repo=repo, run_dir=run_dir, id6="chd001", fake_script_content=script
            )

            # Assert disposition unchanged from today's fail-gate
            self.assertEqual("fail-gate", item["status"])
            attempt = item["attempts"][-1]
            self.assertEqual("fail-gate", attempt["disposition"])

            # Assert host_error recorded on attempt and item
            expected_host_err = {
                "name": "ContentFilterError",
                "message": "The response was blocked by the provider's content filter",
            }
            self.assertEqual(expected_host_err, attempt.get("host_error"))
            self.assertEqual(expected_host_err, item.get("host_error"))

            # Assert preserved lane reason and retention codes in state.json
            self.assertEqual(
                "review turn failed: host ContentFilterError: The response was blocked by the provider's content filter",
                item.get("preserved_reason"),
            )
            self.assertEqual(
                [lane_containment.RETENTION_REVIEW_HOST_ERROR],
                item.get("preserved_retention_reasons"),
            )

            # Assert events.jsonl
            events_path = run_dir / "events.jsonl"
            events = [
                json.loads(line)
                for line in events_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            preserved_events = [
                e for e in events if e.get("event") == "worktree-preserved"
            ]
            self.assertEqual(1, len(preserved_events))
            self.assertEqual(
                "review turn failed: host ContentFilterError: The response was blocked by the provider's content filter",
                preserved_events[0].get("reason"),
            )
            self.assertEqual(
                [lane_containment.RETENTION_REVIEW_HOST_ERROR],
                preserved_events[0].get("retention_reasons"),
            )

            # Summary table text has host error line under item bullet
            summary_table = render_stream.render_run_summary_table(state, "test-driver")
            self.assertIn(
                "host error: ContentFilterError: The response was blocked by the provider's content filter",
                summary_table,
            )

            # Report text has host error
            runner_shared.write_report(
                run_dir, state, labels=runner_shared.OC_HOST_LABELS
            )
            report_text = (run_dir / "execution-report.md").read_text(encoding="utf-8")
            self.assertIn(
                "host ContentFilterError: The response was blocked by the provider's content filter",
                report_text,
            )

    def test_case_b_child_review_silent_exit_1(self) -> None:
        """Case (b): exits 1 silently on a child review."""
        with tempfile.TemporaryDirectory() as temp:
            tmp = pathlib.Path(temp)
            repo, _plan_file, run_dir = self._setup_repo_and_plan(
                tmp, id6="chd002", kind="child"
            )

            script = "#!/usr/bin/env python3\nimport sys\nsys.exit(1)\n"
            item, _state = self._run_fake_review(
                repo=repo, run_dir=run_dir, id6="chd002", fake_script_content=script
            )

            self.assertEqual("fail-gate", item["status"])
            attempt = item["attempts"][-1]
            self.assertIsNone(attempt.get("host_error"))
            self.assertIsNone(item.get("host_error"))

            # Preserved lane reason names exit code, NOT orchestrator readiness
            self.assertEqual(
                "review turn exited 1 with no outcome file",
                item.get("preserved_reason"),
            )
            self.assertEqual(
                [lane_containment.RETENTION_REVIEW_TURN_EXITED],
                item.get("preserved_retention_reasons"),
            )
            self.assertNotIn("orchestrator", str(item.get("preserved_reason")))

    def test_case_c_orchestrator_review_readiness_fails(self) -> None:
        """Case (c): exits 0 on an orchestrator whose readiness fails."""
        with tempfile.TemporaryDirectory() as temp:
            tmp = pathlib.Path(temp)
            repo, _plan_file, run_dir = self._setup_repo_and_plan(
                tmp, id6="orc001", kind="orchestrator"
            )

            # Script exits 0 and writes an event so positive evidence check passes
            script = (
                "#!/usr/bin/env python3\n"
                "import json, sys\n"
                "print(json.dumps({'type':'text','part':{'text':'reviewed'}}))\n"
                "sys.exit(0)\n"
            )
            item, _state = self._run_fake_review(
                repo=repo,
                run_dir=run_dir,
                id6="orc001",
                fake_script_content=script,
                readiness_ready=False,
                extra_options={"retry_budget": 0},
            )

            self.assertEqual("fail-gate", item["status"])
            self.assertEqual(
                "review orchestrator readiness failed; lane preserved for inspection",
                item.get("preserved_reason"),
            )
            self.assertEqual(
                [lane_containment.RETENTION_REVIEW_ORCHESTRATOR_FAILED],
                item.get("preserved_retention_reasons"),
            )

    def test_case_d_orchestrator_review_exit_1(self) -> None:
        """Case (d): exits 1 on an orchestrator review (handler must not evaluate)."""
        with tempfile.TemporaryDirectory() as temp:
            tmp = pathlib.Path(temp)
            repo, _plan_file, run_dir = self._setup_repo_and_plan(
                tmp, id6="orc002", kind="orchestrator"
            )

            script = "#!/usr/bin/env python3\nimport sys\nsys.exit(1)\n"
            item, _state = self._run_fake_review(
                repo=repo,
                run_dir=run_dir,
                id6="orc002",
                fake_script_content=script,
                readiness_ready=False,
            )

            self.assertEqual("fail-gate", item["status"])
            # Handler did not evaluate; reason is turn exited 1, NOT orchestrator failed
            self.assertEqual(
                "review turn exited 1 with no outcome file",
                item.get("preserved_reason"),
            )
            self.assertEqual(
                [lane_containment.RETENTION_REVIEW_TURN_EXITED],
                item.get("preserved_retention_reasons"),
            )
            self.assertNotIn("orchestrator", str(item.get("preserved_reason")))


if __name__ == "__main__":
    unittest.main()
