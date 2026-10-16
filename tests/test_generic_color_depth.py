"""Tests for generic color depth handling (IPD lv0dvv / backlog cvtg9u).

Verifies that the color_depth configuration pin and terminal capability detection
govern the generic color axis (Term.colorize, Term.color256, status_256, badge,
path, severity_label, format_fix), ensuring:
- pin 'none' emits no ANSI escape sequences on generic styling
- pin '16' maps xterm-256 indices to basic 16-color ANSI SGR codes without 38;5; sequences
- pin '256' retains today's 38;5;N sequences
- unpinned 16-color terminals (such as TERM=vt100) degrade to 16-color ANSI SGR
"""

from __future__ import annotations

import argparse
from collections import Counter
import io
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from agent_workflows import config as CFG
from agent_workflows import pwatch, render_stream, runners_monitor
from agent_workflows import term as T


class _FakeTTY(io.StringIO):
    def isatty(self) -> bool:
        return True


class _FakePipe(io.StringIO):
    def isatty(self) -> bool:
        return False


class _DepthTestBase(unittest.TestCase):
    def setUp(self) -> None:
        self._saved = {
            k: os.environ.get(k)
            for k in (
                "NO_COLOR",
                "FORCE_COLOR",
                "TERM",
                "COLORTERM",
                "XDG_CONFIG_HOME",
                "AW_HOME",
                "AW_NO_REEXEC",
            )
        }
        self._tmp = tempfile.TemporaryDirectory()
        os.environ["XDG_CONFIG_HOME"] = self._tmp.name
        self.addCleanup(self._tmp.cleanup)
        self.addCleanup(self._restore_env)
        self.addCleanup(T.set_color_override, None)
        try:
            sigint = signal.getsignal(signal.SIGINT)
            sigterm = signal.getsignal(signal.SIGTERM)
            self.addCleanup(signal.signal, signal.SIGINT, sigint)
            self.addCleanup(signal.signal, signal.SIGTERM, sigterm)
        except ValueError:
            pass

    def _restore_env(self) -> None:
        for k, v in self._saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    def _capable_tty(self) -> None:
        for k in ("NO_COLOR", "FORCE_COLOR", "COLORTERM"):
            os.environ.pop(k, None)
        os.environ["TERM"] = "xterm-256color"
        T.set_color_override(None)
        cfg = CFG.load()
        if "color_depth" in cfg:
            cfg.pop("color_depth")
            CFG.save(cfg)

    def _pin(self, value: str) -> None:
        CFG.set_config_value("color_depth", value)


class GenericColorDepthTests(_DepthTestBase):
    """Behavioral tests verifying the generic color axis honors color_depth."""

    def test_cell_a_pin_none_fake_tty(self) -> None:
        """Cell (a): pin none on fake TTY returns plain text with words intact."""
        self._capable_tty()
        self._pin("none")
        t = T.Term(stream=_FakeTTY())

        helpers = [
            ("status_256", t.status_256("up to date"), "up to date"),
            ("path", t.path("a/b"), "a/b"),
            ("badge", t.badge("x", "error"), "x"),
            ("colorize", t.colorize("x", "bold"), "x"),
            ("severity_label", t.severity_label("error"), "ERROR"),
            ("format_fix", t.format_fix("do it"), "do it"),
        ]
        for name, styled, word in helpers:
            with self.subTest(helper=name):
                self.assertNotIn(
                    "\033", styled, f"{name} emitted escape sequence at pin none"
                )
                self.assertIn(word, styled, f"{name} missing word at pin none")

    def test_cell_b_pin_16_fake_tty(self) -> None:
        """Cell (b): pin 16 on fake TTY styles with basic ANSI and no 38;5;."""
        self._capable_tty()
        self._pin("16")
        t = T.Term(stream=_FakeTTY())

        helpers = [
            ("status_256", t.status_256("up to date")),
            ("path", t.path("a/b")),
            ("badge", t.badge("x", "error")),
            ("colorize", t.colorize("x", "bold")),
            ("severity_label", t.severity_label("error")),
            ("format_fix", t.format_fix("do it")),
        ]
        for name, styled in helpers:
            with self.subTest(helper=name):
                self.assertIn("\033", styled, f"{name} not styled at pin 16")
                self.assertNotIn("38;5;", styled, f"{name} emitted 38;5; at pin 16")

        # status_256("error") and status_256("up to date") render different SGR codes
        s_err = t.status_256("error")
        s_ok = t.status_256("up to date")
        codes_err = re.findall(r"\033\[([0-9;]*)m", s_err)
        codes_ok = re.findall(r"\033\[([0-9;]*)m", s_ok)
        self.assertNotEqual(
            codes_err, codes_ok, "error and ok must use different SGR codes"
        )

    def test_cell_c_pin_256_bytes_identical(self) -> None:
        """Cell (c): pin 256 on fake TTY is byte-identical to 256-color output."""
        self._capable_tty()
        self._pin("256")
        t = T.Term(stream=_FakeTTY())
        self.assertEqual(
            t.status_256("up to date"),
            "\x1b[1;38;5;46mup to date\x1b[0m",
        )
        self.assertEqual(
            t.path("a/b"),
            "\x1b[38;5;33ma/b\x1b[0m",
        )

    def test_cell_d_no_color_beats_pin_256(self) -> None:
        """Cell (d): NO_COLOR=1 with pin 256 still yields plain text."""
        self._capable_tty()
        self._pin("256")
        os.environ["NO_COLOR"] = "1"
        t = T.Term(stream=_FakeTTY())
        self.assertFalse(t.color)
        self.assertEqual(t.status_256("up to date"), "up to date")
        self.assertEqual(t.path("a/b"), "a/b")
        self.assertNotIn("\033", t.status_256("up to date"))
        self.assertNotIn("\033", t.path("a/b"))

    def test_cell_e_pipe_color_true_pin_16(self) -> None:
        """Cell (e): Term(stream=<fake pipe>, color=True) with pin 16 resolves 16 rather than none."""
        self._capable_tty()
        self._pin("16")
        t = T.Term(stream=_FakePipe(), color=True)
        self.assertEqual(t.lifecycle_depth(), T.DEPTH_16)
        self.assertNotEqual(t.lifecycle_depth(), T.DEPTH_NONE)
        self.assertTrue(t.color)
        self.assertIn("\033", t.status_256("up to date"))

    def test_cell_f_color_16_for_index_mapping(self) -> None:
        """Cell (f): color_16_for_index reduction covers all 256 indices and preserves live mappings."""
        candidate_set = {
            T._SGR_RED,
            T._SGR_GREEN,
            T._SGR_YELLOW,
            T._SGR_BLUE,
            T._SGR_MAGENTA,
            T._SGR_CYAN,
            T._SGR_WHITE,
            T._SGR_BRIGHT_BLACK,
            T._SGR_BRIGHT_GREEN,
            T._SGR_BRIGHT_YELLOW,
            T._SGR_BRIGHT_MAGENTA,
            T._SGR_BRIGHT_CYAN,
        }
        # Access as module attribute inside test method per PR-004
        color_16_fn = getattr(T, "color_16_for_index")

        for i in range(256):
            res = color_16_fn(i)
            self.assertIn(
                res,
                candidate_set,
                f"Index {i} mapped to {res} which is outside candidate set",
            )

        live_expected = {
            196: 31,
            203: 31,
            46: 92,
            40: 32,
            226: 93,
            220: 93,
            214: 33,
            208: 33,
            39: 36,
            33: 36,
            36: 36,
            44: 36,
            207: 95,
            244: 90,
            245: 90,
            250: 37,
            255: 37,
        }
        for idx, expected_sgr in live_expected.items():
            with self.subTest(index=idx):
                self.assertEqual(
                    color_16_fn(idx),
                    expected_sgr,
                    f"Live index {idx} mapped to {color_16_fn(idx)}, expected {expected_sgr}",
                )

    def test_cell_g_subprocess_end_to_end(self) -> None:
        """Cell (g): end-to-end CLI commands index plans and check at pins none, 16, 256."""
        repo_root = str(Path(__file__).resolve().parent.parent)

        with tempfile.TemporaryDirectory() as fixture_dir, tempfile.TemporaryDirectory() as tmp_home:
            subprocess.run(["git", "init", "-q"], cwd=fixture_dir, check=True)

            plans_dir = Path(fixture_dir) / ".aw" / "records" / "plans" / "pending"
            plans_dir.mkdir(parents=True, exist_ok=True)

            backlog_dir = Path(fixture_dir) / ".aw" / "records" / "backlog" / "open"
            backlog_dir.mkdir(parents=True, exist_ok=True)
            (backlog_dir / "20261001-test01-01-test01-sample.backlog.md").write_text(
                "# Backlog: Sample\n\n- Id: test01\n- Status: open\n- Set: test01\n- Priority: low\n- Work-Kind: chore\n- Summary: Sample\n\n## Workflow history\n\n- 2026-01-01 created (aw backlog): fixture\n",
                encoding="utf-8",
            )

            child_env = os.environ.copy()
            child_env["XDG_CONFIG_HOME"] = os.path.join(tmp_home, "config")
            child_env["AW_HOME"] = os.path.join(tmp_home, "aw_home")
            child_env["AW_NO_REEXEC"] = "1"
            child_env["TERM"] = "xterm-256color"
            child_env["PYTHONPATH"] = repo_root
            for k in ("NO_COLOR", "FORCE_COLOR", "COLORTERM"):
                child_env.pop(k, None)

            for pin in ("none", "16", "256"):
                subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "agent_workflows",
                        "config",
                        "set",
                        "color_depth",
                        pin,
                    ],
                    cwd=fixture_dir,
                    env=child_env,
                    check=True,
                    capture_output=True,
                )

                for cmd_args in (["index", "plans", "--color"], ["check", "--color"]):
                    res = subprocess.run(
                        [sys.executable, "-m", "agent_workflows", *cmd_args],
                        cwd=fixture_dir,
                        env=child_env,
                        capture_output=True,
                        text=True,
                    )
                    self.assertEqual(
                        res.returncode,
                        0,
                        f"Command {cmd_args} failed at pin {pin}: stderr={res.stderr}",
                    )
                    if pin == "none":
                        self.assertNotIn(
                            "\033",
                            res.stdout,
                            f"Command {cmd_args} emitted escape at pin none",
                        )
                    elif pin == "16":
                        self.assertIn(
                            "\033",
                            res.stdout,
                            f"Command {cmd_args} emitted no escape at pin 16",
                        )
                        self.assertNotIn(
                            "38;5;",
                            res.stdout,
                            f"Command {cmd_args} emitted 38;5; at pin 16",
                        )
                    elif pin == "256":
                        self.assertIn(
                            "38;5;",
                            res.stdout,
                            f"Command {cmd_args} emitted no 38;5; at pin 256",
                        )

    def test_cell_h_unpinned_16_detection(self) -> None:
        """Cell (h): unpinned terminal with TERM=vt100 detects as 16-color on generic axis."""
        self._capable_tty()
        os.environ["TERM"] = "vt100"
        t = T.Term(stream=_FakeTTY())
        out = t.status_256("up to date")
        self.assertIn("\033", out, "Expected ANSI escapes for vt100")
        self.assertNotIn("38;5;", out, "Expected no 38;5; in 16-color detection")


class RawLiteralColorDepthTests(_DepthTestBase):
    """Behavioral tests verifying raw-literal modules honor color_depth (IPD 32fso3).

    Covers pwatch.py, runners_monitor.py, and render_stream.py (Palette.__call__,
    headers, badges, statusline, and run summary table).
    Tests are portable across Linux, macOS, and Windows: no real /proc access.
    """

    @staticmethod
    def _sgr_escapes(text: str) -> list[str]:
        return re.findall(r"\033\[[0-9;]*m", text)

    def _make_process_tree(self) -> dict[int, pwatch.Process]:
        p_root = pwatch.Process(
            pid=100,
            ppid=1,
            name="python3",
            cmdline=("python3", "-m", "agent_workflows", "run"),
        )
        p_c1 = pwatch.Process(
            pid=101,
            ppid=100,
            name="pytest",
            cmdline=("pytest", "-v", "tests/test_a.py"),
            threads=Counter({"worker": 2}),
        )
        p_c2 = pwatch.Process(
            pid=102,
            ppid=100,
            name="pytest",
            cmdline=("pytest", "-v", "tests/test_b.py"),
        )
        p_c3 = pwatch.Process(
            pid=103,
            ppid=100,
            name="bash",
            cmdline=("bash", "-c", "echo hello", "/tmp/foo.txt"),
        )
        p_c4 = pwatch.Process(
            pid=104,
            ppid=100,
            name="agy",
            cmdline=("agy", "run", "all"),
        )
        p_root.children = [p_c1, p_c2, p_c3, p_c4]
        return {
            100: p_root,
            101: p_c1,
            102: p_c2,
            103: p_c3,
            104: p_c4,
        }

    def _make_runners(self) -> list[runners_monitor.RunnerInfo]:
        r_high = runners_monitor.RunnerInfo(
            pid=1001,
            run_id="run-1",
            run_dir=Path("/dummy/1"),
            host="agy",
            step_str="1/2",
            setid="set1",
            id6="id0001",
            action="execute",
            attempt=1,
            status="running",
            activity="pytest (4 procs)",
            cpu_pct=95.0,
            cum_cpu_sec=10.0,
            rss_bytes=1024 * 1024 * 100,
            num_procs=4,
            descendant_pids={1002, 1003},
            total_cpus=4,
        )
        r_mid = runners_monitor.RunnerInfo(
            pid=2001,
            run_id="run-2",
            run_dir=Path("/dummy/2"),
            host="opencode",
            step_str="2/2",
            setid="set2",
            id6="id0002",
            action="review",
            attempt=1,
            status="running",
            activity="idle / coordinating",
            cpu_pct=40.0,
            cum_cpu_sec=5.0,
            rss_bytes=1024 * 1024 * 50,
            num_procs=1,
            descendant_pids=set(),
            total_cpus=4,
        )
        r_low = runners_monitor.RunnerInfo(
            pid=3001,
            run_id="run-3",
            run_dir=Path("/dummy/3"),
            host="agy",
            step_str="1/1",
            setid="set3",
            id6="id0003",
            action="execute",
            attempt=1,
            status="running",
            activity="git status",
            cpu_pct=5.0,
            cum_cpu_sec=1.0,
            rss_bytes=1024 * 1024 * 20,
            num_procs=1,
            descendant_pids=set(),
            total_cpus=4,
        )
        return [r_high, r_mid, r_low]

    def test_pwatch_color_depth_ladder(self) -> None:
        """pwatch coloring ladder across none, 16, 256, NO_COLOR=1, and TERM=vt100."""
        procs = self._make_process_tree()
        rules = [pwatch.Rule.create("python3", pwatch.MatchKind.MATCH_CS)]
        empty_rules = [pwatch.Rule.create("nonexistent", pwatch.MatchKind.MATCH_CS)]
        decorations = {104: "step 1/3 [agy]"}

        self._capable_tty()
        self._pin("256")
        base_color = pwatch.get_process_color(procs[104].name)
        base_arg_flag = pwatch.format_colored_argument("-v", color_enabled=True)
        base_arg_path = pwatch.format_colored_argument(
            "/tmp/foo.txt", color_enabled=True
        )
        base_arg_text = pwatch.format_colored_argument("hello", color_enabled=True)
        base_snap, _ = pwatch.render_snapshot(
            procs,
            rules,
            [],
            max_depth=5,
            width=80,
            color_enabled=True,
            runner_decorations=decorations,
        )
        base_snap_trunc, _ = pwatch.render_snapshot(
            procs,
            rules,
            [],
            max_depth=5,
            width=40,
            color_enabled=True,
            runner_decorations=decorations,
        )

        with patch("agent_workflows.pwatch.read_processes", return_value=procs), patch(
            "agent_workflows.runners_monitor.find_active_runners",
            return_value=[(100, Path("/dummy/run"), "run-1")],
        ), patch(
            "agent_workflows.runners_monitor.extract_journey_info",
            return_value=("1/3", "myset", "abc123", "execute", 1, "agy"),
        ):
            for pin in ("none", "16", "256", "vt100"):
                self._capable_tty()
                if pin == "vt100":
                    os.environ["TERM"] = "vt100"
                else:
                    self._pin(pin)

                c_proc = pwatch.get_process_color(procs[104].name)
                c_flag = pwatch.format_colored_argument("-v", color_enabled=True)
                c_path = pwatch.format_colored_argument(
                    "/tmp/foo.txt", color_enabled=True
                )
                c_text = pwatch.format_colored_argument("hello", color_enabled=True)
                snap, _ = pwatch.render_snapshot(
                    procs,
                    rules,
                    [],
                    max_depth=5,
                    width=80,
                    color_enabled=True,
                    runner_decorations=decorations,
                )
                snap_trunc, _ = pwatch.render_snapshot(
                    procs,
                    rules,
                    [],
                    max_depth=5,
                    width=40,
                    color_enabled=True,
                    runner_decorations=decorations,
                )
                snap_empty, _ = pwatch.render_snapshot(
                    procs, empty_rules, [], max_depth=5, width=80, color_enabled=True
                )

                fake_out_pat = _FakeTTY()
                with patch("sys.stdout", fake_out_pat):
                    ret_pat = pwatch.main(["--once", "python3"])
                self.assertEqual(ret_pat, 0)
                out_pat = fake_out_pat.getvalue()

                fake_out_run = _FakeTTY()
                with patch("sys.stdout", fake_out_run):
                    ret_run = pwatch.main(["--once", "--runners"])
                self.assertEqual(ret_run, 0)
                out_run = fake_out_run.getvalue()

                if pin == "none":
                    for name, s in (
                        ("proc_color", c_proc),
                        ("arg_flag", c_flag),
                        ("arg_path", c_path),
                        ("arg_text", c_text),
                        ("snapshot", snap),
                        ("snapshot_trunc", snap_trunc),
                        ("snapshot_empty", snap_empty),
                        ("main_pat", out_pat),
                        ("main_run", out_run),
                    ):
                        self.assertNotIn(
                            "\033", s, f"pwatch {name} emitted escape at pin none"
                        )
                elif pin in ("16", "vt100"):
                    self.assertIn("\033", c_proc)
                    self.assertNotIn("38;5;", c_proc)
                    self.assertIn("\033", c_flag)
                    self.assertNotIn("38;5;", c_flag)
                    self.assertIn("\033", snap)
                    self.assertNotIn("38;5;", snap)
                    self.assertIn("\033", snap_trunc)
                    self.assertNotIn("38;5;", snap_trunc)
                    self.assertNotIn("38;5;", snap_empty)

                    sgr_pat = self._sgr_escapes(out_pat)
                    self.assertGreater(len(sgr_pat), 0)
                    self.assertNotIn("38;5;", out_pat)

                    sgr_run = self._sgr_escapes(out_run)
                    self.assertGreater(len(sgr_run), 0)
                    self.assertNotIn("38;5;", out_run)
                elif pin == "256":
                    self.assertEqual(c_proc, base_color)
                    self.assertEqual(c_flag, base_arg_flag)
                    self.assertEqual(c_path, base_arg_path)
                    self.assertEqual(c_text, base_arg_text)
                    self.assertEqual(snap, base_snap)
                    self.assertEqual(snap_trunc, base_snap_trunc)
                    self.assertIn("38;5;", c_proc)
                    self.assertIn("38;5;", c_flag)
                    self.assertIn("38;5;", snap)
                    self.assertIn("38;5;", out_pat)
                    self.assertIn("38;5;", out_run)

            self._capable_tty()
            self._pin("256")
            os.environ["NO_COLOR"] = "1"

            fake_no_col_pat = _FakeTTY()
            with patch("sys.stdout", fake_no_col_pat):
                self.assertEqual(pwatch.main(["--once", "python3"]), 0)
            self.assertEqual(len(self._sgr_escapes(fake_no_col_pat.getvalue())), 0)

            fake_no_col_run = _FakeTTY()
            with patch("sys.stdout", fake_no_col_run):
                self.assertEqual(pwatch.main(["--once", "--runners"]), 0)
            self.assertEqual(len(self._sgr_escapes(fake_no_col_run.getvalue())), 0)

    def test_runners_monitor_color_depth_ladder(self) -> None:
        """runners_monitor coloring ladder across none, 16, 256, NO_COLOR=1, and TERM=vt100."""
        runners = self._make_runners()
        args = argparse.Namespace(
            repo=".",
            once=True,
            interval=2.0,
            width=120,
            raw_cpu=False,
            json=False,
            agent=False,
            no_color=False,
        )

        with patch(
            "agent_workflows.runners_monitor.sample_runners", return_value=runners
        ):
            for pin in ("none", "16", "256", "vt100"):
                self._capable_tty()
                if pin == "vt100":
                    os.environ["TERM"] = "vt100"
                else:
                    self._pin(pin)

                table = runners_monitor.render_runner_table(runners, color_enabled=True)

                fake_out = _FakeTTY()
                with patch("sys.stdout", fake_out):
                    ret = runners_monitor.run_table_dashboard(args)
                self.assertEqual(ret, 0)
                out = fake_out.getvalue()

                if pin == "none":
                    self.assertNotIn("\033", table)
                    self.assertIn("PID", table)
                    self.assertIn("1001", table)
                    self.assertIn("pytest (4 procs)", table)
                    self.assertNotIn("\033", out)
                    self.assertIn("aw runners", out)
                elif pin in ("16", "vt100"):
                    self.assertIn("\033", table)
                    self.assertNotIn("38;5;", table)
                    sgr_out = self._sgr_escapes(out)
                    self.assertGreater(len(sgr_out), 0)
                    self.assertNotIn("38;5;", out)
                elif pin == "256":
                    self.assertIn("38;5;", table)
                    self.assertIn("38;5;", out)

            self._capable_tty()
            self._pin("256")
            os.environ["NO_COLOR"] = "1"

            fake_no_col = _FakeTTY()
            with patch("sys.stdout", fake_no_col):
                self.assertEqual(runners_monitor.run_table_dashboard(args), 0)
            self.assertEqual(len(self._sgr_escapes(fake_no_col.getvalue())), 0)

    def test_render_stream_headers_statusline_and_palette_color_depth_ladder(
        self,
    ) -> None:
        """render_stream badges, statusline, palette, and summary table color depth ladder."""
        summary_state = {
            "queue": ["32fso3"],
            "plan_actions": {"32fso3": "execute"},
            "items": {
                "32fso3": {
                    "title": "Raw SGR escapes in pwatch",
                    "setid": "y11p5u",
                    "lifecycle_state": "COMPLETED",
                    "duration": 42.0,
                    "cost": 0.12,
                    "tokens": {"total": 1000, "input": 800, "output": 200, "cache": 0},
                    "verify": "pass",
                    "disposition": "executed",
                }
            },
            "spend": {"total_cost": 0.12},
            "tokens": {"total": 1000, "input": 800, "output": 200, "cache": 0},
            "created_at": "2026-10-14T00:00:00Z",
            "updated_at": "2026-10-14T00:00:42Z",
        }

        self._capable_tty()
        self._pin("256")
        base_pal_out = render_stream.Palette(True)("boom", "red", "bold")
        base_prefix_out = render_stream.format_event_prefix(
            "bash", pal=render_stream.Palette(True)
        )
        base_badge_col, _ = render_stream.make_badge(
            "agy", "Gemini 4", "High", color=True
        )
        base_summary = render_stream.render_run_summary_table(
            summary_state, pal=render_stream.Palette(True)
        )

        for pin in ("none", "16", "256", "vt100"):
            self._capable_tty()
            if pin == "vt100":
                os.environ["TERM"] = "vt100"
            else:
                self._pin(pin)

            pal = render_stream.Palette(True)
            styled_text = pal("boom", "red", "bold")
            event_prefix = render_stream.format_event_prefix("bash", pal=pal)
            badge_col, badge_plain = render_stream.make_badge(
                "agy", "Gemini 4", "High", color=True
            )

            summary = render_stream.render_run_summary_table(summary_state, pal=pal)

            for u in (True, False):
                for lvl in (1, 2, 3, 4, "custom"):
                    sc, sp = render_stream.format_stop_badge(
                        lvl, use_unicode=u, color=True
                    )
                    if pin == "none":
                        self.assertEqual(sc, sp)
                        self.assertNotIn("\033", sc)
                    elif pin in ("16", "vt100"):
                        self.assertIn("\033", sc)
                        self.assertNotIn("38;5;", sc)
                        self.assertNotIn("48;5;", sc)
                    elif pin == "256":
                        if u:
                            self.assertIn("48;5;", sc)
                        else:
                            self.assertIn("\033", sc)

                for passed, failed in ((2, 0), (2, 1)):
                    tc, tp = render_stream.format_tally_badge(
                        passed, failed, use_unicode=u, color=True
                    )
                    if pin == "none":
                        self.assertEqual(tc, tp)
                        self.assertNotIn("\033", tc)
                    elif pin in ("16", "vt100"):
                        self.assertIn("\033", tc)
                        self.assertNotIn("38;5;", tc)
                        self.assertNotIn("48;5;", tc)
                    elif pin == "256":
                        self.assertIn("38;5;", tc)

                lines = render_stream.format_statusline_lines(
                    now_ts=1000.0,
                    run_start_ts=900.0,
                    item_start_ts=950.0,
                    last_act_ts=995.0,
                    current_idx=1,
                    total_items=3,
                    setid="y11p5u",
                    id6="32fso3",
                    pal=pal,
                    stall_remaining=120.0,
                    action="execute",
                    use_unicode=u,
                    activity="executing",
                    runner="agy",
                    model="Gemini 4",
                    variant="High",
                    stop_level=1,
                    items_passed=2,
                    items_failed=1,
                    cwd="/repo/test",
                    run_id="run-1",
                )
                plain_lines = render_stream.format_statusline_lines(
                    now_ts=1000.0,
                    run_start_ts=900.0,
                    item_start_ts=950.0,
                    last_act_ts=995.0,
                    current_idx=1,
                    total_items=3,
                    setid="y11p5u",
                    id6="32fso3",
                    pal=render_stream.Palette(False),
                    stall_remaining=120.0,
                    action="execute",
                    use_unicode=u,
                    activity="executing",
                    runner="agy",
                    model="Gemini 4",
                    variant="High",
                    stop_level=1,
                    items_passed=2,
                    items_failed=1,
                    cwd="/repo/test",
                    run_id="run-1",
                )
                self.assertEqual(len(lines), 4)

                if pin == "none":
                    for line_out, line_plain in zip(lines, plain_lines):
                        self.assertNotIn("\033", line_out)
                        self.assertEqual(line_out, line_plain)
                elif pin in ("16", "vt100"):
                    widths = [
                        T.visible_width(render_stream._strip_ansi(line_out))
                        for line_out in lines
                    ]
                    self.assertEqual(
                        len(set(widths)),
                        1,
                        f"Expected rectangular statusline, widths={widths}",
                    )
                    for line_out, line_plain in zip(lines, plain_lines):
                        self.assertIn("\033", line_out)
                        self.assertNotIn("38;5;", line_out)
                        self.assertNotIn("48;5;", line_out)
                        self.assertEqual(
                            render_stream._strip_ansi(line_out), line_plain
                        )
                elif pin == "256":
                    for line_out in lines:
                        self.assertIn("\033", line_out)
                    all_text = "".join(lines)
                    self.assertIn("38;5;", all_text)
                    if u:
                        self.assertIn("48;5;", all_text)

            if pin == "none":
                self.assertEqual(styled_text, "boom")
                self.assertNotIn("\033", styled_text)
                self.assertNotIn("\033", event_prefix)
                self.assertEqual(badge_col, badge_plain)
                self.assertNotIn("\033", badge_col)
                self.assertNotIn("\033", summary)
            elif pin in ("16", "vt100"):
                self.assertIn("\033", styled_text)
                self.assertNotIn("38;5;", styled_text)
                self.assertIn("\033", event_prefix)
                self.assertNotIn("38;5;", event_prefix)
                self.assertIn("\033", badge_col)
                self.assertNotIn("38;5;", badge_col)
                self.assertNotIn("48;5;", badge_col)
                self.assertIn("\033", summary)
                self.assertNotIn("38;5;", summary)
                self.assertNotIn("48;5;", summary)
            elif pin == "256":
                self.assertEqual(styled_text, base_pal_out)
                self.assertEqual(event_prefix, base_prefix_out)
                self.assertEqual(badge_col, base_badge_col)
                self.assertEqual(summary, base_summary)
                self.assertIn("38;5;", badge_col)


if __name__ == "__main__":
    unittest.main()
