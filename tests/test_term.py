"""Tests for agent_workflows.term accessible styling (IPD-2 Batch D; AC-15)."""

from __future__ import annotations

import io
import os
import re
import unittest

from agent_workflows import term as T

_ANSI = re.compile(r"\033\[[0-9;]*m")


class _FakeTTY(io.StringIO):
    def isatty(self):
        return True


class _FakePipe(io.StringIO):
    def isatty(self):
        return False


class ShouldColorTests(unittest.TestCase):
    def setUp(self):
        self._saved = {
            k: os.environ.get(k) for k in ("NO_COLOR", "FORCE_COLOR", "TERM")
        }

    def tearDown(self):
        for k, v in self._saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    def _clear(self):
        for k in ("NO_COLOR", "FORCE_COLOR"):
            os.environ.pop(k, None)
        os.environ["TERM"] = "xterm-256color"

    def test_no_color_disables_on_a_tty(self):
        self._clear()
        os.environ["NO_COLOR"] = "1"
        self.assertFalse(T.should_color(_FakeTTY()))

    def test_force_color_overrides_no_color(self):
        self._clear()
        os.environ["NO_COLOR"] = "1"
        os.environ["FORCE_COLOR"] = "1"
        self.assertTrue(T.should_color(_FakePipe()))

    def test_non_tty_is_plain_by_default(self):
        self._clear()
        self.assertFalse(T.should_color(_FakePipe()))

    def test_tty_gets_color(self):
        self._clear()
        self.assertTrue(T.should_color(_FakeTTY()))

    def test_term_dumb_disables(self):
        self._clear()
        os.environ["TERM"] = "dumb"
        self.assertFalse(T.should_color(_FakeTTY()))


class StylingTests(unittest.TestCase):
    def test_colorize_plain_when_color_off(self):
        t = T.Term(stream=io.StringIO(), color=False)
        self.assertEqual(t.colorize("hi", "red", "bold"), "hi")

    def test_colorize_wraps_when_color_on(self):
        t = T.Term(stream=io.StringIO(), color=True)
        out = t.colorize("hi", "red")
        self.assertRegex(out, _ANSI)
        self.assertIn("hi", out)

    def test_status_word_present_in_plain_mode(self):
        s = io.StringIO()
        t = T.Term(stream=s, color=False)
        t.status("fail", "something broke")
        text = s.getvalue()
        self.assertNotRegex(text, _ANSI)
        self.assertIn("FAIL", text)
        self.assertIn("something broke", text)

    def test_status_word_present_even_with_color(self):
        s = io.StringIO()
        t = T.Term(stream=s, color=True)
        t.status("ok", "done")
        # The WORD is still there alongside color (never color-only).
        self.assertIn("OK", _ANSI.sub("", s.getvalue()))

    def test_color256_plain_when_off(self):
        t = T.Term(stream=io.StringIO(), color=False)
        self.assertEqual(t.color256("hi", 39, bold=True), "hi")

    def test_color256_emits_256_code_when_on(self):
        t = T.Term(stream=io.StringIO(), color=True)
        out = t.color256("hi", 39)
        self.assertIn("\033[38;5;39m", out)
        self.assertIn("hi", out)
        self.assertTrue(out.endswith("\033[0m"))
        # text survives once escapes are stripped
        self.assertEqual(_ANSI.sub("", out), "hi")

    def test_color256_bold_prefix(self):
        t = T.Term(stream=io.StringIO(), color=True)
        self.assertIn("\033[1;38;5;203m", t.color256("x", 203, bold=True))

    def test_color256_clamps_out_of_range(self):
        t = T.Term(stream=io.StringIO(), color=True)
        self.assertIn("38;5;255m", t.color256("x", 999))
        self.assertIn("38;5;0m", t.color256("x", -5))

    def test_status_256_styling_and_padding(self):
        t_color = T.Term(stream=io.StringIO(), color=True)
        out = t_color.status_256("open", width=12)
        self.assertIn("\033[1;38;5;40mopen\033[0m", out)
        self.assertEqual(len(_ANSI.sub("", out)), 12)

        t_plain = T.Term(stream=io.StringIO(), color=False)
        out_plain = t_plain.status_256("open", width=12)
        self.assertEqual(out_plain, "open        ")

    def test_status_palette_consistency_with_attention(self):
        from agent_workflows import attention as att

        for status, code in att._STATUS_COLOR_256.items():
            self.assertIn(status, T.STATUS_COLOR_256)
            self.assertEqual(
                T.STATUS_COLOR_256[status],
                code,
                f"Mismatch for status '{status}': term has {T.STATUS_COLOR_256.get(status)}, attention has {code}",
            )


if __name__ == "__main__":
    unittest.main()
