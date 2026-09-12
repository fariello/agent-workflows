"""Tests for P14 severity labels, Term.status_label fixed-width padding, doctor consumption, and universal --agent machine flags."""

from __future__ import annotations

import pytest

import io
import json
import re
import tempfile
import types
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from agent_workflows import cli, doctor
from agent_workflows import term as T

# Heavy subprocess/CLI suite; excluded from the fast default run (see pyproject addopts
# `-m "not slow"`). Run with `make test-all`.
pytestmark = pytest.mark.slow

_ANSI = re.compile(r"\033\[[0-9;]*m")


class TermSeverityLabelTests(unittest.TestCase):
    """E-01 / V-01: Term.severity_label bracketed fixed-width alignment and color policy."""

    def test_severity_label_color_on(self):
        term = T.Term(color=True)
        # Error: bold red (xterm 196)
        err = term.severity_label("error")
        self.assertEqual(err, "[" + term.color256("ERROR", 196, bold=True) + "]")
        self.assertIn("\033[1;38;5;196mERROR\033[0m", err)
        self.assertTrue(err.startswith("["))
        self.assertTrue(err.endswith("]"))

        # Warn: bold yellow (xterm 226) with trailing space
        warn = term.severity_label("warn")
        self.assertEqual(warn, "[" + term.color256("WARN ", 226, bold=True) + "]")
        self.assertIn("\033[1;38;5;226mWARN \033[0m", warn)

        # Warning alias
        warning = term.severity_label("warning")
        self.assertEqual(warning, warn)

        # Info: bold green (xterm 46) with trailing space
        info = term.severity_label("info")
        self.assertEqual(info, "[" + term.color256("INFO ", 46, bold=True) + "]")
        self.assertIn("\033[1;38;5;46mINFO \033[0m", info)

        # Visible text width alignment (excluding ANSI escape codes)
        self.assertEqual(len(_ANSI.sub("", err)), 7)
        self.assertEqual(len(_ANSI.sub("", warn)), 7)
        self.assertEqual(len(_ANSI.sub("", info)), 7)
        self.assertEqual(_ANSI.sub("", err), "[ERROR]")
        self.assertEqual(_ANSI.sub("", warn), "[WARN ]")
        self.assertEqual(_ANSI.sub("", info), "[INFO ]")

    def test_severity_label_color_off(self):
        term = T.Term(color=False)
        err = term.severity_label("error")
        warn = term.severity_label("warn")
        info = term.severity_label("info")

        self.assertEqual(err, "[ERROR]")
        self.assertEqual(warn, "[WARN ]")
        self.assertEqual(info, "[INFO ]")
        self.assertIsNone(_ANSI.search(err))
        self.assertIsNone(_ANSI.search(warn))
        self.assertIsNone(_ANSI.search(info))

        # Padded fixed-width alignment
        self.assertEqual(len(err), 7)
        self.assertEqual(len(warn), 7)
        self.assertEqual(len(info), 7)

    def test_severity_label_fallback(self):
        term = T.Term(color=False)
        custom = term.severity_label("other")
        self.assertEqual(custom, "[OTHER]")


class TermStatusLabelPaddingTests(unittest.TestCase):
    """`Term.status_label` pads to the labels `status()` ACTUALLY emits (7), not to the widest key.

    NARROWED 2026-09-12 on maintainer request ("OK             " wasted terminal real estate). The
    original width was 13, taken from `NOT-INSTALLED`, the longest entry in `_STATUS_STYLE`. But
    `NOT-INSTALLED` is never passed to `status()`: measured across every call site, only fail/info/
    ok/skip/warn/ignored are, and the currency words render through `_status_badge_256` in tables
    that do their own layout. So the old padding aligned these lines against a label that never
    appears on them, costing 6 columns on all of them.

    Alignment among the labels that DO share these lines is preserved, which is what the padding is
    for.
    """

    def test_status_label_pads_to_the_widest_STATUS_LINE_label(self):
        term = T.Term(color=False)
        width = len("IGNORED")  # the longest label `status()` emits
        self.assertEqual(T._STATUS_WIDTH, width)

        self.assertEqual(term.status_label("ok"), "OK     ")
        self.assertEqual(term.status_label("info"), "INFO   ")
        self.assertEqual(term.status_label("skip"), "SKIP   ")
        self.assertEqual(term.status_label("warn"), "WARN   ")
        self.assertEqual(term.status_label("fail"), "FAIL   ")
        self.assertEqual(term.status_label("ignored"), "IGNORED")
        for key in T._STATUS_LINE_LABELS:
            self.assertEqual(len(term.status_label(key)), width, key)

    def test_a_label_longer_than_the_width_is_never_truncated(self):
        """A currency word still renders IN FULL; it is simply not padded to.

        Truncating would destroy meaning, which the whole word-first convention exists to protect.
        """

        term = T.Term(color=False)
        self.assertEqual(term.status_label("not-installed"), "NOT-INSTALLED")
        self.assertEqual(term.status_label("current"), "CURRENT")

    def test_status_label_padded_with_color(self):
        term = T.Term(color=True)
        lbl_ok = term.status_label("ok")

        self.assertEqual(len(_ANSI.sub("", lbl_ok)), len("IGNORED"))
        self.assertIn("OK", _ANSI.sub("", lbl_ok))
        # The visible word is colored; the padding is not inside the escape sequence.
        self.assertTrue(lbl_ok.endswith("     "), repr(lbl_ok))

    def test_status_method_message_column_aligns(self):
        buf = io.StringIO()
        term = T.Term(stream=buf, color=False)
        term.status("ok", "/path/to/repo_a")
        term.status("warn", "/path/to/repo_b")
        term.status("ignored", "/path/to/repo_c")

        lines = buf.getvalue().splitlines()
        self.assertEqual(len(lines), 3)
        # 7-char status word, 2 spaces, then the message at column 9.
        self.assertEqual(lines[0], "OK       /path/to/repo_a")
        self.assertEqual(lines[1], "WARN     /path/to/repo_b")
        self.assertEqual(lines[2], "IGNORED  /path/to/repo_c")
        for line in lines:
            self.assertEqual(line.find("/path"), 9)

    def test_status_style_includes_severity_entries(self):
        self.assertIn("error", T._STATUS_STYLE)
        self.assertIn("warn", T._STATUS_STYLE)
        self.assertIn("info", T._STATUS_STYLE)


class YesNoSuffixTests(unittest.TestCase):
    """`term.yes_no_suffix` is the ONE renderer for interactive yes/no prompt suffixes.

    Added 2026-09-12 with the maintainer's request to bold the default. The invariant worth pinning
    is that CASE carries the meaning and BOLD is only a redundant cue, so a pipe, `NO_COLOR`, a dumb
    terminal and a screen reader all keep the information.
    """

    def test_monochrome_renders_plain_case_only(self):
        mono = T.Term(color=False)
        self.assertEqual(T.yes_no_suffix(True, term=mono), "[Y/n]")
        self.assertEqual(T.yes_no_suffix(False, term=mono), "[y/N]")

    def test_color_bolds_only_the_default_letter(self):
        color = T.Term(color=True)
        yes = T.yes_no_suffix(True, term=color)
        no = T.yes_no_suffix(False, term=color)

        # Stripped of ANSI, identical to the monochrome rendering: no information lives in color.
        self.assertEqual(_ANSI.sub("", yes), "[Y/n]")
        self.assertEqual(_ANSI.sub("", no), "[y/N]")
        # The emphasized letter is the DEFAULT one, not both.
        self.assertIn("\033[1mY\033[0m".replace("\033", "\x1b"), yes)
        self.assertIn("\033[1mN\033[0m".replace("\033", "\x1b"), no)
        self.assertNotIn("\x1b[1mn", yes)
        self.assertNotIn("\x1b[1my", no)

    def test_the_wizard_and_the_cli_share_this_renderer(self):
        """A second implementation is how the two flows drift apart, so assert one source."""

        from agent_workflows import cli as C, runner_profile_wizard as W

        mono = T.Term(color=False)
        self.assertEqual(C._yes_no(True, mono), "[Y/n]")

        script_prompts = []

        class _IO:
            ask = staticmethod(lambda p: (script_prompts.append(p), "y")[1])
            emit = staticmethod(lambda *_a, **_k: None)

            def line(self, *_a, **_k):
                return None

        io = W.WizardIO(
            ask=lambda p: (script_prompts.append(p), "y")[1], emit=lambda *_a: None
        )
        W.ask_yes_no(io, "Q?", default=True)
        self.assertTrue(script_prompts and "[Y/n]" in script_prompts[0], script_prompts)


class DoctorSeveritySourceTests(unittest.TestCase):
    """E-02 / V-02: doctor.py single-sources severity labels from Term and has no private tag helpers."""

    def test_doctor_has_no_private_tag_helpers(self):
        self.assertFalse(hasattr(doctor, "tag_error"))
        self.assertFalse(hasattr(doctor, "tag_warn"))
        self.assertFalse(hasattr(doctor, "tag_info"))

    def test_doctor_renders_term_severity_labels(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".aw" / "records").mkdir(parents=True)
            out_color = io.StringIO()
            with redirect_stdout(out_color), redirect_stderr(io.StringIO()):
                term_color = T.Term(color=True)
                doctor.run(
                    types.SimpleNamespace(dir=str(root), as_agent=False),
                    term=term_color,
                )
            text_color = out_color.getvalue()
            # Contains bold color escape sequences inside bracketed labels
            self.assertTrue(
                "[ERROR]" in _ANSI.sub("", text_color)
                or "[WARN ]" in _ANSI.sub("", text_color)
                or "[INFO ]" in _ANSI.sub("", text_color)
            )

            out_plain = io.StringIO()
            with redirect_stdout(out_plain), redirect_stderr(io.StringIO()):
                term_plain = T.Term(color=False)
                doctor.run(
                    types.SimpleNamespace(dir=str(root), as_agent=False),
                    term=term_plain,
                )
            text_plain = out_plain.getvalue()
            self.assertIsNone(_ANSI.search(text_plain))
            self.assertTrue(
                "[ERROR]" in text_plain
                or "[WARN ]" in text_plain
                or "[INFO ]" in text_plain
            )


class MachineOutputFlagsTests(unittest.TestCase):
    """E-04 / V-04: Universal --agent flag across read verbs with byte-stable output."""

    def _run_cli(self, argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            try:
                rc = cli.main(argv)
            except SystemExit as e:
                rc = int(e.code or 0)
        return rc, out.getvalue(), err.getvalue()

    def test_status_agent_emits_json(self):
        rc_agent, out_agent, err_agent = self._run_cli(["status", "--agent"])
        self.assertEqual(rc_agent, 0, err_agent)
        data_agent = json.loads(out_agent)
        self.assertEqual(data_agent["schema"], "aw.agent/v1")
        self.assertEqual(data_agent["cmd"], "status")

        rc_json, out_json, err_json = self._run_cli(["status", "--json"])
        self.assertEqual(rc_json, 0, err_json)
        data_json = json.loads(out_json)
        self.assertIn("data", data_json)
        self.assertIn("packaged_version", data_json["data"])

    def test_list_repos_agent_emits_json(self):
        rc_agent, out_agent, err_agent = self._run_cli(["list-repos", "--agent"])
        self.assertEqual(rc_agent, 0, err_agent)
        data_agent = json.loads(out_agent)
        self.assertEqual(data_agent["schema"], "aw.agent/v1")
        self.assertEqual(data_agent["cmd"], "list-repos")

        rc_json, out_json, err_json = self._run_cli(["list-repos", "--json"])
        self.assertEqual(rc_json, 0, err_json)
        data_json = json.loads(out_json)
        self.assertIn("data", data_json)
        self.assertIn("repos", data_json["data"])

    def test_doctor_agent_emits_agent_v1(self):
        rc, out, err = self._run_cli(["doctor", "--agent"])
        self.assertIn(rc, (0, 1))
        lines = [line for line in out.splitlines() if line.strip()]
        if lines:
            data = json.loads(lines[0])
            self.assertEqual(data.get("schema"), "aw.agent/v1")
            self.assertEqual(data.get("cmd"), "doctor")
            self.assertIn("exit", data)

    def test_doctor_accepts_json_flag(self):
        rc, out, err = self._run_cli(["doctor", "--json"])
        self.assertIn(rc, (0, 1))
        data = json.loads(out)
        self.assertIn("command", data)

    def test_backlog_check_agent_accepted(self):
        rc, out, err = self._run_cli(["backlog", "check", "--agent"])
        self.assertIn(rc, (0, 1))

    def test_backlog_check_accepts_json_flag(self):
        rc, out, err = self._run_cli(["backlog", "check", "--json"])
        self.assertIn(rc, (0, 1))
        data = json.loads(out)
        self.assertIn("command", data)

    def test_help_states_agent_format_per_verb(self):
        rc_s, out_s, _ = self._run_cli(["status", "--help"])
        self.assertEqual(rc_s, 0)
        self.assertIn("--agent", out_s)
        self.assertIn("JSON", out_s)

        rc_lr, out_lr, _ = self._run_cli(["list-repos", "--help"])
        self.assertEqual(rc_lr, 0)
        self.assertIn("--agent", out_lr)
        self.assertIn("JSON", out_lr)

        rc_d, out_d, _ = self._run_cli(["doctor", "--help"])
        self.assertEqual(rc_d, 0)
        self.assertIn("--agent", out_d)


if __name__ == "__main__":
    unittest.main()
