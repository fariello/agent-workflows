"""Behavioral tests for capped-pill Ctrl-C menu, batch worktree cleanup, and per-lane cards."""

from __future__ import annotations

import io
import json
import os
import shutil
import subprocess
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

from agent_workflows import (
    render_stream,
    runner_shared,
    runner_stop,
    term,
    worktree_lease,
)
from tests.record_builder import RecordBuilder


def _git(repo: Path, *args: str) -> str:
    res = subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )
    return res.stdout.strip()


def _init_temp_repo(tmp: Path) -> Path:
    repo = tmp / "repo"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test User")
    (repo / "README.md").write_text("hello\n", encoding="utf-8")
    _git(repo, "add", "README.md")
    _git(repo, "commit", "-m", "init")
    return repo


def _create_dirty_lane(
    repo: Path,
    lane_id: str,
    *,
    plan_rel: str,
    short_desc: str,
    dirty_filename: str,
    mtime_offset_seconds: float = 0.0,
) -> tuple[worktree_lease.WorktreeHandle, dict[str, str]]:
    handle = worktree_lease.allocate_worktree(repo, lane_id=lane_id, base_commit="main")
    plan_file = handle.path / plan_rel
    plan_file.parent.mkdir(parents=True, exist_ok=True)
    plan_file.write_text(
        RecordBuilder().plan(
            title=lane_id,
            id6=lane_id,
            set="test-set",
            short_description=short_desc,
            text_only=True,
        ),
        encoding="utf-8",
    )
    dirty_file = handle.path / dirty_filename
    dirty_file.write_text(f"work in {lane_id}\n" * 64, encoding="utf-8")
    if mtime_offset_seconds:
        target_t = time.time() - mtime_offset_seconds
        os.utime(dirty_file, (target_t, target_t))
        os.utime(plan_file, (target_t, target_t))
        os.utime(handle.path, (target_t, target_t))
    return handle, {
        "lane_id": lane_id,
        "id6": lane_id,
        "branch": handle.branch,
        "worktree": str(handle.path),
        "base_sha": handle.base_commit,
    }


class CappedPillCtrlCMenuTests(unittest.TestCase):
    """Verify the Ctrl-C menu uses the statusline-style capped pill header and stays rectangular."""

    def test_unicode_capped_pill_plain_and_rectangular(self) -> None:
        out = io.StringIO()
        with mock.patch.dict(os.environ, {"NO_COLOR": "1", "LANG": "en_US.UTF-8"}):
            action = runner_stop.prompt_interrupt_action(
                stdin=io.StringIO("1\n"), stream=out
            )
        self.assertEqual(action, runner_stop.INTERRUPT_ACTION_RESUME)
        rendered = out.getvalue()
        self.assertIn("\ue0b6 Stopped on Ctrl-C. Choose an action: \ue0b4", rendered)
        box_lines = [
            line for line in rendered.splitlines() if line.startswith(("╭─", "│", "╰"))
        ]
        self.assertEqual(len(box_lines), 6)
        widths = [term.visible_width(line) for line in box_lines]
        self.assertEqual(widths, [62] * 6)

    def test_unicode_capped_pill_with_256_color(self) -> None:
        pill_colored, pill_plain = render_stream.format_capped_pill(
            "Stopped on Ctrl-C. Choose an action:",
            bg_code=214,
            use_unicode=True,
            color=True,
            depth=term.DEPTH_256,
        )
        self.assertIn("\033[38;5;214m\ue0b6\033[48;5;214m", pill_colored)
        self.assertIn("\ue0b4\033[0m", pill_colored)
        self.assertEqual(
            term.visible_width(pill_colored), term.visible_width(pill_plain)
        )

        box = render_stream.render_capped_box(
            "Stopped on Ctrl-C. Choose an action:",
            ["  1. Resume?"],
            inner_width=60,
            pill_bg_code=214,
            use_unicode=True,
            color=True,
            depth=term.DEPTH_256,
        )
        widths = [term.visible_width(line) for line in box.splitlines()]
        self.assertEqual(widths, [62, 62, 62])

    def test_ascii_fallback_box_is_rectangular(self) -> None:
        box = render_stream.render_capped_box(
            "Stopped on Ctrl-C. Choose an action:",
            ["  1. Resume?", "  3. Clean up and exit?"],
            inner_width=60,
            use_unicode=False,
            color=False,
        )
        lines = box.splitlines()
        self.assertTrue(lines[0].startswith("+-[Stopped on Ctrl-C. Choose an action:]"))
        widths = [term.visible_width(line) for line in lines]
        self.assertEqual(widths, [62] * 4)


class BatchWorktreePromptTests(unittest.TestCase):
    """Verify the 5-option capped-pill batch worktree cleanup menu."""

    def test_plural_header_and_all_five_choices(self) -> None:
        lanes = [{"lane_id": f"lane{i:02d}", "holds_work": True} for i in range(11)]
        expected = {
            "1\n": "keep-all",
            "2\n": "discard-interrupted",
            "3\n": "discard-all",
            "4\n": "ask-each",
            "5\n": "cancel-resume",
            "\n": "keep-all",
        }
        with mock.patch.dict(os.environ, {"NO_COLOR": "1", "LANG": "en_US.UTF-8"}):
            for raw_in, want in expected.items():
                out = io.StringIO()
                got = runner_shared.prompt_worktree_batch_action(
                    lanes,
                    interrupted_lane_id="i29bd5",
                    allow_resume=True,
                    stdin=io.StringIO(raw_in),
                    stream=out,
                )
                self.assertEqual(got, want, f"input {raw_in!r}")
                rendered = out.getvalue()
                self.assertIn(
                    "\ue0b6 There are 11 worktrees with work in them. Choose an action: \ue0b4",
                    rendered,
                )
                self.assertIn("(i29bd5)", rendered)
                self.assertIn("Cancel, and resume the work.", rendered)
                box_lines = [
                    line
                    for line in rendered.splitlines()
                    if line.startswith(("╭─", "│", "╰"))
                ]
                self.assertEqual(len(box_lines), 7)
                self.assertEqual(
                    len({term.visible_width(line) for line in box_lines}), 1
                )

    def test_singular_header_and_invalid_input_retry(self) -> None:
        lanes = [{"lane_id": "i29bd5", "holds_work": True}]
        out = io.StringIO()
        with mock.patch.dict(os.environ, {"NO_COLOR": "1", "LANG": "en_US.UTF-8"}):
            got = runner_shared.prompt_worktree_batch_action(
                lanes,
                interrupted_lane_id="i29bd5",
                allow_resume=True,
                stdin=io.StringIO("9\n2\n"),
                stream=out,
            )
        self.assertEqual(got, "discard-interrupted")
        rendered = out.getvalue()
        self.assertIn(
            "There is 1 worktree with work in it. Choose an action:", rendered
        )
        self.assertIn("Please enter 1, 2, 3, 4, or 5:", rendered)

    def test_disabled_or_empty_returns_none(self) -> None:
        out = io.StringIO()
        self.assertIsNone(
            runner_shared.prompt_worktree_batch_action(
                [{"lane_id": "abc123", "holds_work": True}],
                disabled=True,
                stdin=io.StringIO("1\n"),
                stream=out,
            )
        )
        self.assertEqual(out.getvalue(), "")
        self.assertIsNone(
            runner_shared.prompt_worktree_batch_action(
                [], stdin=io.StringIO("1\n"), stream=out
            )
        )


class PerLaneCardPromptTests(unittest.TestCase):
    """Verify the 80-120 column capped-pill per-lane card."""

    def test_card_width_scales_80_to_120_and_displays_metadata(self) -> None:
        lane = {
            "lane_id": "id2pdx",
            "id6": "id2pdx",
            "setid": "companion-bugs",
            "branch": "aw/lane/id2pdx",
            "holds_work": True,
            "is_interrupted_lane": True,
            "age_str": "6h09m old",
            "short_description": "Fix split-brain companion records",
            "last_modified_str": "2026-11-21 01:37:14",
            "size_str": "1.7MB",
            "commits_ahead": 2,
            "dirty": True,
            "item_status": "running",
            "worktree_rel": ".aw/worktrees/id2pdx",
            "prompt_index": 1,
            "prompt_total": 11,
        }
        for term_cols, expected_w in ((80, 80), (100, 98), (150, 120)):
            out = io.StringIO()
            with (
                mock.patch.dict(os.environ, {"NO_COLOR": "1", "LANG": "en_US.UTF-8"}),
                mock.patch.object(
                    shutil,
                    "get_terminal_size",
                    return_value=os.terminal_size((term_cols, 24)),
                ),
            ):
                choice = runner_shared.lane_reclaim_prompt(
                    lane,
                    "keep and snapshot",
                    disabled=False,
                    timeout=5.0,
                    stdin=io.StringIO("d\n"),
                    stream=out,
                )
            self.assertEqual(choice, "discard")
            rendered = out.getvalue()
            self.assertIn("id6: id2pdx", rendered)
            self.assertIn("Setid: companion-bugs", rendered)
            self.assertIn("6h09m old", rendered)
            self.assertIn("[INTERRUPTED]", rendered)
            self.assertIn("Lane aw/lane/id2pdx HOLDS WORK!", rendered)
            self.assertIn("[1/11]", rendered)
            self.assertIn("Desc: Fix split-brain companion records", rendered)
            self.assertIn("Last Modified: 2026-11-21 01:37:14", rendered)
            self.assertIn("Size: 1.7MB", rendered)
            self.assertIn("k = Keep and snapshot (default).", rendered)
            self.assertIn("d = Discard (delete worktree; branch kept).", rendered)
            box_lines = [
                line
                for line in rendered.splitlines()
                if line.startswith(("╭─", "│", "╰"))
            ]
            widths = [term.visible_width(line) for line in box_lines]
            self.assertTrue(all(w == expected_w for w in widths), (term_cols, widths))

    def test_minimal_lane_dict_is_accepted_cleanly(self) -> None:
        out = io.StringIO()
        with mock.patch.dict(os.environ, {"NO_COLOR": "1", "LANG": "en_US.UTF-8"}):
            choice = runner_shared.lane_reclaim_prompt(
                {"lane_id": "abc123", "branch": "aw/lane/abc123", "holds_work": True},
                "keep and snapshot",
                disabled=False,
                timeout=5.0,
                stdin=io.StringIO("k\n"),
                stream=out,
            )
        self.assertEqual(choice, "keep")
        self.assertIn("Lane aw/lane/abc123 HOLDS WORK!", out.getvalue())


class InteractiveInterruptAndReclaimEndToEndTests(unittest.TestCase):
    """End-to-end tests with real git worktrees for option 5 resume, batch policies, and ordering."""

    def _build_two_lane_fixture(
        self, tmp: Path
    ) -> tuple[
        Path,
        Path,
        dict[str, object],
        worktree_lease.WorktreeHandle,
        worktree_lease.WorktreeHandle,
    ]:
        repo = _init_temp_repo(tmp)
        run_dir = tmp / "run-01"
        run_dir.mkdir()
        h_old, rec_old = _create_dirty_lane(
            repo,
            "60mazt",
            plan_rel=".aw/records/plans/pending/20261121-test-01-60mazt-older.ipd.md",
            short_desc="Older stranded worktree",
            dirty_filename="old_work.txt",
            mtime_offset_seconds=7200.0,
        )
        h_cur, rec_cur = _create_dirty_lane(
            repo,
            "i29bd5",
            plan_rel=".aw/records/plans/pending/20261121-test-02-i29bd5-current.ipd.md",
            short_desc="Currently interrupted worktree",
            dirty_filename="cur_work.txt",
            mtime_offset_seconds=5.0,
        )
        state: dict[str, object] = {
            "run_id": "run-01",
            "repo": str(repo),
            "queue": [
                {
                    "id6": "60mazt",
                    "setid": "test",
                    "path": ".aw/records/plans/pending/20261121-test-01-60mazt-older.ipd.md",
                    "status": "failed",
                    "attempts": [
                        {
                            "lane_id": "60mazt",
                            "started_at": "2026-11-21T01:00:00Z",
                            "worktree": rec_old["worktree"],
                            "branch": rec_old["branch"],
                            "base_sha": rec_old["base_sha"],
                        }
                    ],
                },
                {
                    "id6": "i29bd5",
                    "setid": "test",
                    "path": ".aw/records/plans/pending/20261121-test-02-i29bd5-current.ipd.md",
                    "status": "running",
                    "attempts": [
                        {
                            "lane_id": "i29bd5",
                            "started_at": "2026-11-21T07:00:00Z",
                            "worktree": rec_cur["worktree"],
                            "branch": rec_cur["branch"],
                            "base_sha": rec_cur["base_sha"],
                        }
                    ],
                },
            ],
        }
        (run_dir / "state.json").write_text(json.dumps(state), encoding="utf-8")
        return repo, run_dir, state, h_old, h_cur

    def test_ctrlc_choice_3_then_batch_option_5_resumes_without_killing_child(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as td:
            _repo, run_dir, _state, _h_old, _h_cur = self._build_two_lane_fixture(
                Path(td)
            )
            fake_child = mock.MagicMock()
            out = io.StringIO()
            actions_seen: list[int] = []

            with (
                mock.patch.dict(os.environ, {"NO_COLOR": "1", "LANG": "en_US.UTF-8"}),
                mock.patch.object(
                    runner_stop, "pause_live_children", return_value=[fake_child]
                ),
                mock.patch.object(runner_stop, "resume_live_children") as mock_resume,
                mock.patch(
                    "agent_workflows.runner_shutdown.clean_shutdown"
                ) as mock_shutdown,
            ):
                result = runner_stop.handle_interactive_interrupt(
                    run_dir=run_dir,
                    stdin=io.StringIO("3\n5\n"),
                    stream=out,
                    on_action=actions_seen.append,
                )

            self.assertEqual(result, runner_stop.INTERRUPT_ACTION_RESUME)
            self.assertEqual(actions_seen, [runner_stop.INTERRUPT_ACTION_RESUME])
            mock_resume.assert_called_once_with([fake_child])
            mock_shutdown.assert_not_called()
            self.assertEqual(
                runner_shared.pop_pending_lane_reclaim_policy(run_dir), (None, None)
            )
            rendered = out.getvalue()
            self.assertIn("There are 2 worktrees with work in them.", rendered)
            self.assertIn("(i29bd5)", rendered)
            self.assertIn("Resuming...", rendered)

    def test_discard_interrupted_policy_keeps_older_and_discards_only_interrupted(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo, run_dir, state, h_old, h_cur = self._build_two_lane_fixture(Path(td))
            runner_shared.set_pending_lane_reclaim_policy(
                run_dir, "discard-interrupted", interrupted_lane_id="i29bd5"
            )
            prompt_calls: list[str] = []

            def _fake_prompt(lane: dict[str, object], default_action: str) -> str:
                prompt_calls.append(str(lane.get("lane_id")))
                return "keep"

            lanes = runner_shared.reclaim_lanes_on_interrupt(
                repo,
                run_dir,
                state,
                interactive=True,
                lane_prompt=_fake_prompt,
                disable_prompt=lambda: None,
            )
            self.assertEqual(prompt_calls, [])
            by_id = {lane["lane_id"]: lane for lane in lanes}
            self.assertEqual(by_id["i29bd5"]["action"], "reclaimed")
            self.assertEqual(by_id["60mazt"]["action"], "preserved")
            self.assertFalse(h_cur.path.exists())
            self.assertTrue(h_old.path.exists())

    def test_keep_all_and_discard_all_policies_skip_per_lane_prompt(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo, run_dir, state, h_old, h_cur = self._build_two_lane_fixture(Path(td))
            runner_shared.set_pending_lane_reclaim_policy(
                run_dir, "keep-all", interrupted_lane_id="i29bd5"
            )
            prompt_calls: list[str] = []
            lanes = runner_shared.reclaim_lanes_on_interrupt(
                repo,
                run_dir,
                state,
                interactive=True,
                lane_prompt=lambda lane, _d: (
                    prompt_calls.append(lane["lane_id"]),
                    "discard",
                )[1],
                disable_prompt=lambda: None,
            )
            self.assertEqual(prompt_calls, [])
            self.assertTrue(h_old.path.exists())
            self.assertTrue(h_cur.path.exists())
            self.assertTrue(all(lane["action"] == "preserved" for lane in lanes))

            # Now run discard-all on the same two lanes.
            runner_shared.set_pending_lane_reclaim_policy(
                run_dir, "discard-all", interrupted_lane_id="i29bd5"
            )
            lanes2 = runner_shared.reclaim_lanes_on_interrupt(
                repo,
                run_dir,
                state,
                interactive=True,
                lane_prompt=lambda lane, _d: (
                    prompt_calls.append(lane["lane_id"]),
                    "keep",
                )[1],
                disable_prompt=lambda: None,
            )
            self.assertEqual(prompt_calls, [])
            self.assertFalse(h_old.path.exists())
            self.assertFalse(h_cur.path.exists())
            self.assertTrue(all(lane["action"] == "reclaimed" for lane in lanes2))

    def test_ask_each_presents_interrupted_lane_first_with_enriched_metadata(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo, run_dir, state, _h_old, _h_cur = self._build_two_lane_fixture(
                Path(td)
            )
            runner_shared.set_pending_lane_reclaim_policy(
                run_dir, "ask-each", interrupted_lane_id="i29bd5"
            )
            seen_lanes: list[dict[str, object]] = []

            def _capture_prompt(lane: dict[str, object], _default: str) -> str:
                seen_lanes.append(dict(lane))
                return "keep"

            runner_shared.reclaim_lanes_on_interrupt(
                repo,
                run_dir,
                state,
                interactive=True,
                lane_prompt=_capture_prompt,
                disable_prompt=lambda: None,
            )
            self.assertEqual(
                [lane["lane_id"] for lane in seen_lanes], ["i29bd5", "60mazt"]
            )
            first, second = seen_lanes
            self.assertTrue(first["is_interrupted_lane"])
            self.assertFalse(second["is_interrupted_lane"])
            self.assertEqual(first["prompt_index"], 1)
            self.assertEqual(first["prompt_total"], 2)
            self.assertEqual(second["prompt_index"], 2)
            self.assertEqual(second["prompt_total"], 2)
            self.assertEqual(
                first["short_description"], "Currently interrupted worktree"
            )
            self.assertEqual(second["short_description"], "Older stranded worktree")
            self.assertTrue(str(first.get("last_modified_str") or ""))
            self.assertTrue(str(first.get("age_str") or "").endswith("old"))
            self.assertTrue(str(first.get("size_str") or ""))


if __name__ == "__main__":
    unittest.main()
