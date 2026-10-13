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

import io
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

from agent_workflows import config as CFG
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
                "# Backlog: Sample\n\n- Id: test01\n- Status: open\n- Set: test01\n- Priority: low\n- Work-Kind: chore\n- Summary: Sample\n",
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


if __name__ == "__main__":
    unittest.main()
