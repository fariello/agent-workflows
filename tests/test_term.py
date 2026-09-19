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


class ColorPrecedenceTests(unittest.TestCase):
    """THE PRECEDENCE TABLE, pinned: flag beats env beats detection (ttyflags `yaxr4i` E-03).

    Slots into the existing env/isatty harness above rather than building a new one; the only new
    ingredient is the `override=` parameter that carries the `--color`/`--no-color` flag layer.

    WHY THE FLAG LAYER TAKES AN ARGUMENT INSTEAD OF SETTING AN ENV VAR, since that is the design
    decision these tests protect: this package spawns nested `aw` processes, and an environment
    variable would be INHERITED, so a parent's terminal choice would silently restyle a child's
    output. `test_no_env_mutation` is the assertion that keeps that from being reintroduced.
    """

    def setUp(self):
        self._saved = {
            k: os.environ.get(k) for k in ("NO_COLOR", "FORCE_COLOR", "TERM")
        }
        self.addCleanup(self._restore)
        self.addCleanup(T.set_color_override, None)
        for k in ("NO_COLOR", "FORCE_COLOR"):
            os.environ.pop(k, None)
        os.environ["TERM"] = "xterm-256color"

    def _restore(self):
        for k, v in self._saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    # --- rung 1: the flag beats the env, in BOTH directions -------------------------------------
    def test_color_flag_beats_no_color_env(self):
        os.environ["NO_COLOR"] = "1"
        self.assertTrue(T.should_color(_FakeTTY(), override=True))
        self.assertTrue(T.should_color(_FakePipe(), override=True))

    def test_no_color_flag_beats_force_color_env(self):
        os.environ["FORCE_COLOR"] = "1"
        self.assertFalse(T.should_color(_FakeTTY(), override=False))
        self.assertFalse(T.should_color(_FakePipe(), override=False))

    def test_no_color_flag_beats_a_capable_tty(self):
        self.assertFalse(T.should_color(_FakeTTY(), override=False))

    def test_color_flag_beats_term_dumb(self):
        os.environ["TERM"] = "dumb"
        self.assertTrue(T.should_color(_FakeTTY(), override=True))

    # --- rung 2: the env beats detection when NO flag is passed ---------------------------------
    def test_env_beats_detection_without_a_flag(self):
        os.environ["FORCE_COLOR"] = "1"
        self.assertTrue(T.should_color(_FakePipe()))
        os.environ.pop("FORCE_COLOR")
        os.environ["NO_COLOR"] = "1"
        self.assertFalse(T.should_color(_FakeTTY()))

    # --- rung 3: detection alone, with neither flag nor env -------------------------------------
    def test_detection_alone_with_neither_flag_nor_env(self):
        self.assertTrue(T.should_color(_FakeTTY()))
        self.assertFalse(T.should_color(_FakePipe()))

    # --- the process-wide override, and the no-leak invariant -----------------------------------
    def test_process_wide_override_applies_and_resets(self):
        T.set_color_override(True)
        self.assertTrue(T.should_color(_FakePipe()))
        self.assertEqual(T.get_color_override(), True)
        T.set_color_override(None)
        self.assertFalse(T.should_color(_FakePipe()))
        self.assertIsNone(T.get_color_override())

    def test_explicit_argument_beats_the_process_wide_override(self):
        T.set_color_override(False)
        self.assertTrue(T.should_color(_FakePipe(), override=True))

    def test_no_env_mutation(self):
        before = {k: os.environ.get(k) for k in ("NO_COLOR", "FORCE_COLOR", "TERM")}
        T.set_color_override(True)
        T.should_color(_FakePipe())
        T.set_color_override(False)
        T.should_color(_FakeTTY())
        after = {k: os.environ.get(k) for k in ("NO_COLOR", "FORCE_COLOR", "TERM")}
        self.assertEqual(before, after)

    # --- the flag pair is read in ONE place ----------------------------------------------------
    def test_color_override_reads_the_flag_pair_from_a_namespace(self):
        import argparse as _argparse

        self.assertIsNone(T.color_override(None))
        self.assertIsNone(
            T.color_override(_argparse.Namespace(no_color=False, color=False))
        )
        self.assertTrue(
            T.color_override(_argparse.Namespace(no_color=False, color=True))
        )
        self.assertFalse(
            T.color_override(_argparse.Namespace(no_color=True, color=False))
        )
        # A hand-built namespace carrying BOTH (argparse refuses this structurally) resolves to
        # the SAFE direction: never invent escapes a caller may not be able to render.
        self.assertFalse(
            T.color_override(_argparse.Namespace(no_color=True, color=True))
        )

    def test_the_256_color_path_is_reached_by_the_same_boolean(self):
        """The maintainer asked for 256-color, and no new capability tier is needed: `color256`
        and the 16-color `colorize` are gated by the SAME `self.color` boolean, so `--color` sets
        one thing. A distinct 16-vs-256 tier is a separate question and is deliberately not here."""

        forced = T.Term(
            stream=_FakePipe(), color=T.should_color(_FakePipe(), override=True)
        )
        self.assertTrue(forced.color)
        self.assertRegex(forced.color256("hi", 46), _ANSI)
        self.assertIn("38;5;46", forced.color256("hi", 46))
        self.assertRegex(forced.colorize("hi", "red"), _ANSI)

        plain = T.Term(
            stream=_FakeTTY(), color=T.should_color(_FakeTTY(), override=False)
        )
        self.assertFalse(plain.color)
        self.assertEqual(plain.color256("hi", 46), "hi")
        self.assertEqual(plain.colorize("hi", "red"), "hi")


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
