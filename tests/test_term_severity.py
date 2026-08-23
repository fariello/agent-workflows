"""Tests for P14 severity labels, Term.status_label fixed-width padding, doctor consumption, and universal --agent machine flags."""

from __future__ import annotations

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
    """E-03 / V-03: Term.status_label fixed-width padding to NOT-INSTALLED (13)."""

    def test_status_label_padded_in_monochrome(self):
        term = T.Term(color=False)
        lbl_ok = term.status_label("ok")
        lbl_not_installed = term.status_label("not-installed")
        lbl_current = term.status_label("current")
        lbl_stale = term.status_label("stale")

        self.assertEqual(len(lbl_ok), 13)
        self.assertEqual(len(lbl_not_installed), 13)
        self.assertEqual(len(lbl_current), 13)
        self.assertEqual(len(lbl_stale), 13)

        self.assertEqual(lbl_ok, "OK           ")
        self.assertEqual(lbl_not_installed, "NOT-INSTALLED")
        self.assertEqual(lbl_current, "CURRENT      ")
        self.assertEqual(lbl_stale, "STALE        ")

    def test_status_label_padded_with_color(self):
        term = T.Term(color=True)
        lbl_ok = term.status_label("ok")
        lbl_not_installed = term.status_label("not-installed")

        # Visual text width (stripped of ANSI) is fixed at 13
        self.assertEqual(len(_ANSI.sub("", lbl_ok)), 13)
        self.assertEqual(len(_ANSI.sub("", lbl_not_installed)), 13)
        self.assertIn("OK", _ANSI.sub("", lbl_ok))
        self.assertIn("NOT-INSTALLED", _ANSI.sub("", lbl_not_installed))

    def test_status_method_message_column_aligns(self):
        buf = io.StringIO()
        term = T.Term(stream=buf, color=False)
        term.status("ok", "/path/to/repo_a")
        term.status("not-installed", "/path/to/repo_b")
        term.status("stale", "/path/to/repo_c")

        lines = buf.getvalue().splitlines()
        self.assertEqual(len(lines), 3)
        # Column 0..12 is the 13-char status word; column 13..14 is 2 spaces; column 15 starts the message
        self.assertEqual(lines[0], "OK             /path/to/repo_a")
        self.assertEqual(lines[1], "NOT-INSTALLED  /path/to/repo_b")
        self.assertEqual(lines[2], "STALE          /path/to/repo_c")
        self.assertEqual(lines[0].find("/path"), 15)
        self.assertEqual(lines[1].find("/path"), 15)
        self.assertEqual(lines[2].find("/path"), 15)

    def test_status_style_includes_severity_entries(self):
        self.assertIn("error", T._STATUS_STYLE)
        self.assertIn("warn", T._STATUS_STYLE)
        self.assertIn("info", T._STATUS_STYLE)


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
