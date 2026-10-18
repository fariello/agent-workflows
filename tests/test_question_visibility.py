"""Tests for parked question visibility across runner statusline, terminal bell, and attention.

Implements spec 6kwd2e assertions:
- A10d (R4a.3): Statusline reports parked question counts.
- A10e (R4a.4): Terminal bell emitted once on first park and not again.
- A10f (R4a.5): Terminal bell suppressed when not a TTY, or under --quiet/--raw/agent mode.
- A10g (R4a.6): aw attention reports nonzero parked questions and awaiting-human run state.
- A10h (R4a.6): Parked item artifact status and cross-tree class unchanged.
- A46 (R9.6): Statusline names aw runs answer <run-id>.
"""

from __future__ import annotations

import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Self
from unittest import mock

from agent_workflows import attention as att
from agent_workflows import render_stream, runner_shared, term
from tests.support import REPO_ROOT, init_repo

_HOLDER_CODE = """
import sys
from pathlib import Path
from agent_workflows import platform_lock

held = platform_lock.acquire(Path(sys.argv[1]))
sys.stdout.write("locked\\n")
sys.stdout.flush()
sys.stdin.read()
held.release()
"""


class _HolderProcess:
    """Subprocess holding driver.lock via platform_lock to simulate an active driver."""

    def __init__(self, lock_path: Path, repo_root: Path = REPO_ROOT) -> None:
        self.lock_path = lock_path
        self.repo_root = repo_root
        self.proc: subprocess.Popen | None = None

    def start(self) -> None:
        env = {
            **os.environ,
            "PYTHONPATH": f"{self.repo_root}{os.pathsep}{os.environ.get('PYTHONPATH', '')}".rstrip(
                os.pathsep
            ),
        }
        self.proc = subprocess.Popen(
            [sys.executable, "-c", _HOLDER_CODE, str(self.lock_path)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True,
            env=env,
        )
        assert self.proc.stdout is not None
        line = self.proc.stdout.readline().strip()
        assert line == "locked", f"Holder failed to acquire lock: {line!r}"

    def stop(self) -> None:
        if self.proc is not None:
            if self.proc.poll() is None:
                if self.proc.stdin is not None:
                    try:
                        self.proc.stdin.close()
                    except OSError:
                        pass
                try:
                    self.proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.proc.kill()
                    self.proc.wait(timeout=5)
            self.proc = None

    def __enter__(self) -> Self:
        self.start()
        return self

    def __exit__(self, *args: object) -> None:
        self.stop()


class _MockTtyStringIO(io.StringIO):
    """StringIO subclass that reports isatty() == True."""

    def isatty(self) -> bool:
        return True


def _sample_statusline_lines(**kwargs) -> tuple[str, str, str, str]:
    """Helper to call format_statusline_lines with reasonable defaults."""
    default_kw = {
        "now_ts": 1700000000.0,
        "run_start_ts": 1700000000.0 - 3600.0,
        "item_start_ts": 1700000000.0 - 60.0,
        "last_act_ts": 1700000000.0 - 10.0,
        "current_idx": 4,
        "total_items": 5,
        "setid": "qchan",
        "id6": "it0004",
        "items_passed": 2,
        "items_failed": 0,
        "pal": None,
        "use_unicode": True,
    }
    default_kw.update(kwargs)
    return render_stream.format_statusline_lines(**default_kw)


class TestStatuslineQuestionVisibility(unittest.TestCase):
    """Unit and formatting tests for statusline parked question badge (A10d, A46)."""

    def test_parked_question_count_pure_calculation(self) -> None:
        # None / empty state
        self.assertEqual(runner_shared.parked_question_count(None), 0)
        self.assertEqual(runner_shared.parked_question_count({}), 0)

        # 3 parked items with 1 question each -> reports 3 (A10d)
        state_3_items = {
            "queue": [
                {"id6": "it0001", "status": "awaiting-human", "questions": ["q1"]},
                {"id6": "it0002", "status": "awaiting-human", "question_ids": ["q2"]},
                {
                    "id6": "it0003",
                    "status": "awaiting-human",
                    "questions": [{"id": "q3"}],
                },
                {"id6": "it0004", "status": "running"},
                {"id6": "it0005", "status": "executed"},
            ]
        }
        self.assertEqual(runner_shared.parked_question_count(state_3_items), 3)

        # 1 item with 2 questions -> reports 2 (A10d)
        state_1_item_2_questions = {
            "queue": [
                {
                    "id6": "it0001",
                    "status": "awaiting-human",
                    "questions": ["q1", "q2"],
                },
                {"id6": "it0002", "status": "running"},
            ]
        }
        self.assertEqual(
            runner_shared.parked_question_count(state_1_item_2_questions), 2
        )

        # Items dict fallback when queue not populated
        state_items_dict = {
            "items": {
                "it0001": {
                    "status": "awaiting-human",
                    "question_ids": ["q1", "q2", "q3"],
                },
                "it0002": {"status": "queued"},
            }
        }
        self.assertEqual(runner_shared.parked_question_count(state_items_dict), 3)

    def test_statusline_reports_three_questions_and_names_answer(self) -> None:
        """A10d: Statusline of a run with 3 parked items reports 3; A46: names aw runs answer <run-id>."""
        run_id = "run-20261017T120000Z-111111"
        lines = _sample_statusline_lines(
            run_id=run_id,
            parked_questions=3,
            use_unicode=True,
        )
        joined = "\n".join(lines)
        self.assertIn("3 questions", joined)
        self.assertIn(f"aw runs answer {run_id}", joined)
        self.assertIn("·", joined)  # unicode middot

        # ASCII mode uses dash/hyphen
        lines_ascii = _sample_statusline_lines(
            run_id=run_id,
            parked_questions=3,
            use_unicode=False,
        )
        joined_ascii = "\n".join(lines_ascii)
        self.assertIn("3 questions", joined_ascii)
        self.assertIn(f"aw runs answer {run_id}", joined_ascii)
        self.assertIn("-", joined_ascii)

    def test_statusline_singular_question_rendering(self) -> None:
        run_id = "run-20261017T120000Z-111111"
        lines = _sample_statusline_lines(
            run_id=run_id,
            parked_questions=1,
            use_unicode=True,
        )
        joined = "\n".join(lines)
        self.assertIn("? 1 question ·", joined)

    def test_statusline_zero_questions_byte_identity(self) -> None:
        """With 0 or None parked questions, output must remain byte-identical to default."""
        lines_default = _sample_statusline_lines(run_id="run-20261017T120000Z-111111")
        lines_none = _sample_statusline_lines(
            run_id="run-20261017T120000Z-111111", parked_questions=None
        )
        lines_zero = _sample_statusline_lines(
            run_id="run-20261017T120000Z-111111", parked_questions=0
        )

        self.assertEqual(lines_default, lines_none)
        self.assertEqual(lines_default, lines_zero)

    def test_statusline_rectangularity_and_visible_widths(self) -> None:
        """Statusline must remain strictly rectangular across all badge / length combinations."""
        run_ids = [
            "run-short",
            "run-20261017T120000Z-111111",
            "run-20261017T120000Z-very-long-run-id-string-1234567890",
        ]
        stop_levels = [None, 1, 2, "pause"]
        question_counts = [None, 0, 1, 3, 42]
        use_unicodes = [False, True]

        for rid in run_ids:
            for s_lvl in stop_levels:
                for q_cnt in question_counts:
                    for u_uni in use_unicodes:
                        lines = _sample_statusline_lines(
                            run_id=rid,
                            stop_level=s_lvl,
                            parked_questions=q_cnt,
                            use_unicode=u_uni,
                        )
                        widths = [term.visible_width(line_str) for line_str in lines]
                        self.assertEqual(
                            len(set(widths)),
                            1,
                            f"Non-rectangular statusline with rid={rid}, stop_level={s_lvl}, "
                            f"parked_questions={q_cnt}, unicode={u_uni}: widths={widths}",
                        )
                        # Check that aw runs answer prefix is never truncated even with long run id
                        if q_cnt and q_cnt > 0:
                            joined = "\n".join(lines)
                            self.assertIn("aw runs answer", joined)


class TestBellOnFirstPark(unittest.TestCase):
    """Unit tests for terminal bell on park (A10e, A10f)."""

    def setUp(self) -> None:
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.run_dir = Path(self.tmp_dir.name)
        self.state_file = self.run_dir / "state.json"
        self.state = {
            "run_id": "run-20261017T120000Z-test",
            "options": {"output_mode": "clean", "as_agent": False},
            "events": [],
        }
        self.state_file.write_text(json.dumps(self.state), encoding="utf-8")

    def tearDown(self) -> None:
        self.tmp_dir.cleanup()

    def test_bell_emitted_once_on_tty_stream_across_three_parks_and_after_reload(
        self,
    ) -> None:
        """A10e: Bell emitted once on first park and not again on second or third or after reload."""
        tty_stream = _MockTtyStringIO()

        # Park 1: Bell rings, state updated and saved
        rung1 = runner_shared.ring_bell_on_first_park(
            self.run_dir, self.state, stream=tty_stream
        )
        self.assertTrue(rung1)
        self.assertEqual(tty_stream.getvalue().count("\a"), 1)
        self.assertTrue(self.state.get("bell_rung"))

        # Verify state.json on disk contains bell_rung
        disk_state = json.loads(self.state_file.read_text(encoding="utf-8"))
        self.assertTrue(disk_state.get("bell_rung"))

        # Park 2: Bell does not ring
        rung2 = runner_shared.ring_bell_on_first_park(
            self.run_dir, self.state, stream=tty_stream
        )
        self.assertFalse(rung2)
        self.assertEqual(tty_stream.getvalue().count("\a"), 1)

        # Park 3: Bell does not ring
        rung3 = runner_shared.ring_bell_on_first_park(
            self.run_dir, self.state, stream=tty_stream
        )
        self.assertFalse(rung3)
        self.assertEqual(tty_stream.getvalue().count("\a"), 1)

        # Reload state from disk (simulate resume/restart)
        reloaded_state = json.loads(self.state_file.read_text(encoding="utf-8"))
        rung4 = runner_shared.ring_bell_on_first_park(
            self.run_dir, reloaded_state, stream=tty_stream
        )
        self.assertFalse(rung4)
        self.assertEqual(tty_stream.getvalue().count("\a"), 1)

    def test_bell_suppressed_on_non_tty_stream(self) -> None:
        """A10f: With output stream not a TTY, no bell byte appears anywhere."""
        non_tty_stream = io.StringIO()  # isatty() is False
        rung = runner_shared.ring_bell_on_first_park(
            self.run_dir, self.state, stream=non_tty_stream
        )
        self.assertFalse(rung)
        self.assertEqual(non_tty_stream.getvalue().count("\a"), 0)
        self.assertFalse(self.state.get("bell_rung"))

        # Also test with real OS pipe (non-tty)
        r_fd, w_fd = os.pipe()
        try:
            with open(w_fd, "w", encoding="utf-8", closefd=False) as pipe_w:
                rung_pipe = runner_shared.ring_bell_on_first_park(
                    self.run_dir, self.state, stream=pipe_w
                )
                self.assertFalse(rung_pipe)
                self.assertFalse(self.state.get("bell_rung"))
        finally:
            os.close(w_fd)
            os.close(r_fd)

    def test_bell_suppressed_by_presentation_overrides(self) -> None:
        """A10f: Bell suppressed under --quiet, --raw, and agent mode."""
        # 1. output_mode == "quiet"
        self.state["options"]["output_mode"] = "quiet"
        tty_stream = _MockTtyStringIO()
        rung = runner_shared.ring_bell_on_first_park(
            self.run_dir, self.state, stream=tty_stream
        )
        self.assertFalse(rung)
        self.assertEqual(tty_stream.getvalue().count("\a"), 0)
        self.assertFalse(self.state.get("bell_rung"))

        # 2. output_mode == "raw"
        self.state["options"]["output_mode"] = "raw"
        rung = runner_shared.ring_bell_on_first_park(
            self.run_dir, self.state, stream=tty_stream
        )
        self.assertFalse(rung)
        self.assertEqual(tty_stream.getvalue().count("\a"), 0)
        self.assertFalse(self.state.get("bell_rung"))

        # 3. as_agent == True
        self.state["options"]["output_mode"] = "clean"
        self.state["options"]["as_agent"] = True
        rung = runner_shared.ring_bell_on_first_park(
            self.run_dir, self.state, stream=tty_stream
        )
        self.assertFalse(rung)
        self.assertEqual(tty_stream.getvalue().count("\a"), 0)
        self.assertFalse(self.state.get("bell_rung"))

    def test_bell_oserror_swallowed_and_recorded(self) -> None:
        """An OSError while writing bell is swallowed and recorded in events."""
        failing_stream = _MockTtyStringIO()
        failing_stream.write = mock.Mock(
            side_effect=OSError("Disk full or stream closed")
        )  # type: ignore

        rung = runner_shared.ring_bell_on_first_park(
            self.run_dir, self.state, stream=failing_stream
        )
        self.assertFalse(rung)
        # An event bell-failed should be appended in events.jsonl
        events_file = self.run_dir / "events.jsonl"
        self.assertTrue(events_file.is_file())
        events = [
            json.loads(line)
            for line in events_file.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        event_names = [e.get("event") for e in events]
        self.assertIn("bell-failed", event_names)


class TestAttentionQuestionVisibility(unittest.TestCase):
    """Integration tests for aw attention parked question surfacing (A10g, A10h)."""

    def setUp(self) -> None:
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.repo_root = init_repo(Path(self.tmp_dir.name))
        self.plan_dir = self.repo_root / ".aw" / "records" / "plans" / "pending"
        self.plan_dir.mkdir(parents=True, exist_ok=True)
        self.plan_file = self.plan_dir / "20261017-qchan-01-y1vjzp-test.ipd.md"
        self.initial_plan_content = (
            "# IPD: test plan\n\n"
            "- Date: 2026-10-17\n"
            "- Kind: child\n"
            "- Concern: Test plan\n"
            "- Scope: Test\n"
            "- Status: approved\n"
            "- Readiness: go-pending-approval\n"
            "- Work-Kind: feature\n"
            "- Priority: medium\n"
            "- Set: qchan\n"
            "- Order: 1\n"
            "- Id: y1vjzp\n\n"
            "## Body\nTest\n"
        )
        self.plan_file.write_text(self.initial_plan_content, encoding="utf-8")

        self.runs_dir = self.repo_root / ".aw" / "records" / "runs"
        self.run_id = "run-20261017T220000Z-100"
        self.live_run_dir = self.runs_dir / self.run_id
        self.live_run_dir.mkdir(parents=True, exist_ok=True)

        self.state_data = {
            "run_id": self.run_id,
            "options": {"output_mode": "clean", "as_agent": False},
            "queue": [
                {
                    "id6": "y1vjzp",
                    "status": "awaiting-human",
                    "questions": [{"id": "q1", "text": "Question text"}],
                }
            ],
            "items": {
                "y1vjzp": {
                    "status": "awaiting-human",
                    "questions": [{"id": "q1", "text": "Question text"}],
                }
            },
        }
        (self.live_run_dir / "state.json").write_text(
            json.dumps(self.state_data), encoding="utf-8"
        )
        self.lock_file = self.live_run_dir / "driver.lock"

        self.env = {
            **os.environ,
            "PYTHONPATH": f"{REPO_ROOT}{os.pathsep}{os.environ.get('PYTHONPATH', '')}".rstrip(
                os.pathsep
            ),
        }

    def tearDown(self) -> None:
        self.tmp_dir.cleanup()

    def test_attention_parked_questions_live_run_subprocess(self) -> None:
        """A10g: aw attention reports nonzero parked-question count and awaiting-human run state.

        A10h: Parked item artifact status and cross-tree class are unchanged.
        """
        # Hold driver.lock with helper process
        with _HolderProcess(self.lock_file, repo_root=REPO_ROOT):
            # 1. aw attention --runs (human board)
            res_runs = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agent_workflows",
                    "attention",
                    "--runs",
                    "--no-color",
                ],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                check=False,
                env=self.env,
            )
            self.assertEqual(
                res_runs.returncode, 0, f"attention --runs failed: {res_runs.stderr}"
            )
            self.assertIn("awaiting-human", res_runs.stdout)
            # Must not show the truncated fallback 'awaitin ' or '[run: awaitin]'
            self.assertNotIn("awaitin ", res_runs.stdout)
            self.assertNotIn("[run: awaitin]", res_runs.stdout)
            self.assertNotIn("fail-", res_runs.stdout)
            # Must not fold into blocked class (OQ-01 ruling)
            self.assertNotIn("## blocked", res_runs.stdout)
            self.assertIn("## ready", res_runs.stdout)

            # Footer waiting line present in human output
            expected_notice = f"run {self.run_id}: 1 question waiting; answer with aw runs answer {self.run_id}"
            self.assertIn(expected_notice, res_runs.stdout)

            # 2. aw attention --format json
            res_json = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agent_workflows",
                    "attention",
                    "--format",
                    "json",
                ],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                check=False,
                env=self.env,
            )
            self.assertEqual(res_json.returncode, 0)
            json_data = json.loads(res_json.stdout)
            keys = list(json_data.keys())
            # Assert parked_questions is appended as the last key
            self.assertEqual(
                keys,
                [
                    "schema_version",
                    "mapping_version",
                    "valid",
                    "items",
                    "violations",
                    "stranded_lanes",
                    "parked_questions",
                ],
            )
            self.assertEqual(
                json_data["parked_questions"],
                [{"run_id": self.run_id, "count": 1}],
            )

        # 3. A10h: Verify artifact status is unchanged
        current_content = self.plan_file.read_text(encoding="utf-8")
        self.assertEqual(current_content, self.initial_plan_content)
        self.assertIn("- Status: approved", current_content)

        # Scan artifact through att.scan and verify attention_class is still "ready"
        items, _ = att.scan(self.repo_root)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].id, "y1vjzp")
        self.assertEqual(items[0].native_status, "approved")
        self.assertEqual(items[0].attention_class, "ready")

    def test_attention_parked_questions_dead_run_empty_subprocess(self) -> None:
        """Without a live driver holding driver.lock, parked_questions is empty."""
        res_json_dead = subprocess.run(
            [sys.executable, "-m", "agent_workflows", "attention", "--format", "json"],
            cwd=self.repo_root,
            capture_output=True,
            text=True,
            check=False,
            env=self.env,
        )
        self.assertEqual(res_json_dead.returncode, 0)
        json_data_dead = json.loads(res_json_dead.stdout)
        self.assertEqual(json_data_dead["parked_questions"], [])

    def test_attention_run_status_filters_subprocess(self) -> None:
        """--run-status awaiting-human and --run-status question both filter correctly."""
        with _HolderProcess(self.lock_file, repo_root=REPO_ROOT):
            # 1. Filter --run-status awaiting-human
            res_filter_ah = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agent_workflows",
                    "attention",
                    "--runs",
                    "--run-status",
                    "awaiting-human",
                    "--no-color",
                ],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                check=False,
                env=self.env,
            )
            self.assertEqual(res_filter_ah.returncode, 0)
            self.assertIn("y1vjzp", res_filter_ah.stdout)
            self.assertIn("awaiting-human", res_filter_ah.stdout)

            # 2. Filter --run-status question (short alias)
            res_filter_q = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agent_workflows",
                    "attention",
                    "--runs",
                    "--run-status",
                    "question",
                    "--no-color",
                ],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                check=False,
                env=self.env,
            )
            self.assertEqual(res_filter_q.returncode, 0)
            self.assertIn("y1vjzp", res_filter_q.stdout)
            self.assertIn("awaiting-human", res_filter_q.stdout)


if __name__ == "__main__":
    unittest.main()
