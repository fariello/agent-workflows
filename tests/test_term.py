"""Tests for agent_workflows.term accessible styling (IPD-2 Batch D; AC-15)."""

from __future__ import annotations

import contextlib
import inspect
import io
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

from agent_workflows import cli
from agent_workflows import config as CFG
from agent_workflows import lifecycle_style as LS
from agent_workflows import render_stream
from agent_workflows import term as T

_ANSI = re.compile(r"\033\[[0-9;]*m")


class _FakeTTY(io.StringIO):
    def isatty(self):
        return True


class _FakePipe(io.StringIO):
    def isatty(self):
        return False


class _Utf8TTY(_FakeTTY):
    encoding = "utf-8"


class _Utf8Pipe(_FakePipe):
    encoding = "utf-8"


class _AsciiPipe(_FakePipe):
    encoding = "ascii"


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

    def test_should_color_basics_and_tty(self):
        # NO_COLOR disables on a tty
        self._clear()
        os.environ["NO_COLOR"] = "1"
        self.assertFalse(T.should_color(_FakeTTY()))

        # FORCE_COLOR overrides NO_COLOR
        self._clear()
        os.environ["NO_COLOR"] = "1"
        os.environ["FORCE_COLOR"] = "1"
        self.assertTrue(T.should_color(_FakePipe()))

        # non-tty plain by default
        self._clear()
        self.assertFalse(T.should_color(_FakePipe()))

        # tty gets color
        self._clear()
        self.assertTrue(T.should_color(_FakeTTY()))

        # TERM=dumb disables
        self._clear()
        os.environ["TERM"] = "dumb"
        self.assertFalse(T.should_color(_FakeTTY()))


_ENV_VALUES = (None, "", "0", "1")


def _env_label(value: str | None) -> str:
    return "unset" if value is None else (value if value else "empty")


_COLOR_GRID: dict[tuple[str | None, str | None], tuple[bool, bool]] = {
    (None, None): (True, False),
    (None, ""): (True, False),
    (None, "0"): (True, False),
    (None, "1"): (True, True),
    ("", None): (False, False),
    ("", ""): (False, False),
    ("", "0"): (False, False),
    ("", "1"): (True, True),
    ("0", None): (False, False),
    ("0", ""): (False, False),
    ("0", "0"): (False, False),
    ("0", "1"): (True, True),
    ("1", None): (False, False),
    ("1", ""): (False, False),
    ("1", "0"): (False, False),
    ("1", "1"): (True, True),
}

_TERM_GRID: dict[str | None, tuple[bool, bool]] = {
    "xterm-256color": (True, False),
    "dumb": (False, False),
    "": (False, False),
    None: (False, False),
}


class ShouldColorGridTests(unittest.TestCase):
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

    def _apply(self, **values: str | None) -> None:
        for key, value in values.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    def test_should_color_grid_expectations(self):
        self.assertEqual(len(_COLOR_GRID) * 2, 32)
        # Check every NO_COLOR x FORCE_COLOR combination
        for (no_color, force_color), (on_tty, on_pipe) in _COLOR_GRID.items():
            for stream_kind, stream_cls, expected in (
                ("tty", _FakeTTY, on_tty),
                ("pipe", _FakePipe, on_pipe),
            ):
                case = (
                    f"NO_COLOR={_env_label(no_color)} "
                    f"FORCE_COLOR={_env_label(force_color)} on a {stream_kind}"
                )
                with self.subTest(case=case):
                    self._apply(
                        NO_COLOR=no_color,
                        FORCE_COLOR=force_color,
                        TERM="xterm-256color",
                    )
                    self.assertEqual(
                        T.should_color(stream_cls()),
                        expected,
                        f"{case}: expected {'color' if expected else 'plain'}",
                    )

        # Check every TERM value
        for term_value, (on_tty, on_pipe) in _TERM_GRID.items():
            for stream_kind, stream_cls, expected in (
                ("tty", _FakeTTY, on_tty),
                ("pipe", _FakePipe, on_pipe),
            ):
                case = f"TERM={_env_label(term_value)} on a {stream_kind}"
                with self.subTest(case=case):
                    self._apply(NO_COLOR=None, FORCE_COLOR=None, TERM=term_value)
                    self.assertEqual(
                        T.should_color(stream_cls()),
                        expected,
                        f"{case}: expected {'color' if expected else 'plain'}",
                    )

        # Falsey FORCE_COLOR never forces and never suppresses
        for value in ("", "0", "false", "FALSE", "no", "off", " 0 "):
            with self.subTest(force_color=value):
                self._apply(NO_COLOR=None, FORCE_COLOR=value, TERM="xterm-256color")
                self.assertTrue(T.should_color(_FakeTTY()))
                self.assertFalse(T.should_color(_FakePipe()))

    def test_force_color_falsey_membership(self):
        """Assert exact canonical membership of T._FORCE_COLOR_FALSEY."""
        expected = frozenset({"", "0", "false", "no", "off"})
        self.assertEqual(
            T._FORCE_COLOR_FALSEY,
            expected,
            f"Unexpected _FORCE_COLOR_FALSEY: {T._FORCE_COLOR_FALSEY ^ expected}",
        )

    def test_force_color_extended_falsey_and_forcing(self):
        """Extended falsey coverage and forcing-side normalization (E-04)."""

        def spellings_for(base: str) -> list[str]:
            if base == "":
                return ["", "  ", "\t"]
            elif base == "0":
                return ["0", " 0 ", "  0 \t"]
            else:
                return [base, base.upper(), f" {base.capitalize()} "]

        required_members = {"", "0", "false", "no", "off"}
        # Drive candidate members from T._FORCE_COLOR_FALSEY itself, joined with required members
        all_bases = sorted(set(T._FORCE_COLOR_FALSEY) | required_members)

        # 1. Falsey coverage across all members, variants, NO_COLOR states, stream kinds
        for base in all_bases:
            for spelling in spellings_for(base):
                for no_color in ("1", None):
                    for stream_kind, stream_cls in (
                        ("tty", _FakeTTY),
                        ("pipe", _FakePipe),
                    ):
                        expected = (
                            False if no_color is not None else (stream_kind == "tty")
                        )
                        case = (
                            f"spelling={spelling!r} NO_COLOR={no_color} "
                            f"on {stream_kind} (base={base!r})"
                        )
                        with self.subTest(case=case):
                            self._apply(
                                NO_COLOR=no_color,
                                FORCE_COLOR=spelling,
                                TERM="xterm-256color",
                            )
                            self.assertEqual(
                                T.should_color(stream_cls()),
                                expected,
                                f"{case}: expected {'color' if expected else 'plain'}",
                            )

        # 2. Forcing-side normalization: truthy values needing stripping or case-folding
        forcing_cases = [
            (" 1 ", "pipe", _FakePipe, None, True),
            (" 1 ", "pipe", _FakePipe, "1", True),
            (" 1 ", "tty", _FakeTTY, "1", True),
            ("TRUE", "pipe", _FakePipe, None, True),
            ("TRUE", "pipe", _FakePipe, "1", True),
            ("On", "pipe", _FakePipe, None, True),
            ("On", "pipe", _FakePipe, "1", True),
            ("2", "pipe", _FakePipe, None, True),
            ("2", "pipe", _FakePipe, "1", True),
            (" true ", "pipe", _FakePipe, None, True),
            (" true ", "pipe", _FakePipe, "1", True),
            (" YES ", "pipe", _FakePipe, None, True),
            (" YES ", "pipe", _FakePipe, "1", True),
        ]
        for force_val, stream_kind, stream_cls, no_color, expected in forcing_cases:
            case = f"FORCE_COLOR={force_val!r} NO_COLOR={no_color} on {stream_kind}"
            with self.subTest(case=case):
                self._apply(
                    NO_COLOR=no_color,
                    FORCE_COLOR=force_val,
                    TERM="xterm-256color",
                )
                self.assertEqual(
                    T.should_color(stream_cls()),
                    expected,
                    f"{case}: expected {'color' if expected else 'plain'}",
                )


class WorkedCasesContractTests(unittest.TestCase):
    """Pin the published color precedence contract table in docs/cli-output-contract.md.

    This test reads a `docs/` prose table, which is repository CONTENT, and asserts
    that the published claim is TRUE by executing `term.should_color`, the subject the
    document describes. It does NOT assert that any production source text or structure
    is unchanged (no inspect.getsource, no ast.parse over agent_workflows/, no assertIn
    over a package file), honoring the 2026-09-26 maintainer ruling against source pins
    (backlog xelvyi, plan 96xtmi).
    """

    def setUp(self):
        self._saved = {
            k: os.environ.get(k) for k in ("NO_COLOR", "FORCE_COLOR", "TERM")
        }
        self.addCleanup(self._restore)
        self.addCleanup(T.set_color_override, None)

    def _restore(self):
        for k, v in self._saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    def test_worked_cases_table_matches_should_color(self):
        doc_path = (
            Path(__file__).resolve().parent.parent / "docs" / "cli-output-contract.md"
        )
        content = doc_path.read_text(encoding="utf-8")

        lines = content.splitlines()
        in_table = False
        table_lines = []
        for line in lines:
            if "Worked cases, each pinned by a test in" in line:
                in_table = True
                continue
            if in_table:
                stripped = line.strip()
                if not stripped:
                    if table_lines:
                        break
                    continue
                if stripped.startswith("|"):
                    table_lines.append(stripped)
                elif table_lines:
                    break

        rows = []
        for line in table_lines:
            raw_cells = re.split(r"(?<!\\)\|", line)
            cells = [c.strip() for c in raw_cells[1:-1]]
            if (
                len(cells) < 2
                or cells[0] == "Invocation"
                or set(cells[0]) <= {"-", " "}
            ):
                continue

            raw_invoc, raw_result = cells[0], cells[1]
            invoc = raw_invoc.strip("`").strip().replace(r"\|", "|")
            tokens = invoc.split()

            env = {}
            i = 0
            while (
                i < len(tokens) and "=" in tokens[i] and not tokens[i].startswith("--")
            ):
                var, val = tokens[i].split("=", 1)
                env[var] = val
                i += 1

            if "=" in invoc:
                self.assertTrue(
                    env,
                    f"Row contains '=' but extracted environment was empty: {raw_invoc!r}",
                )

            override = None
            if "--no-color" in tokens:
                override = False
            elif "--color" in tokens:
                override = True

            is_tty = not (
                invoc.endswith("| cat")
                or (len(tokens) >= 2 and tokens[-2:] == ["|", "cat"])
            )
            expected_colored = raw_result.startswith("colored")

            rows.append(
                {
                    "raw_invoc": raw_invoc,
                    "invoc": invoc,
                    "env": env,
                    "override": override,
                    "is_tty": is_tty,
                    "expected": expected_colored,
                    "raw_result": raw_result,
                }
            )

        # (d) Fail loudly rather than vacuously: row floor and required rows
        self.assertGreaterEqual(
            len(rows),
            11,
            f"Expected at least 11 rows in worked cases table, found {len(rows)}",
        )
        invoc_texts = [r["invoc"] for r in rows]
        self.assertTrue(
            any(
                "NO_COLOR=1 FORCE_COLOR=0" in inv and "| cat" not in inv
                for inv in invoc_texts
            ),
            "Missing required row: 'NO_COLOR=1 FORCE_COLOR=0' on a TTY",
        )
        self.assertTrue(
            any(
                inv == "FORCE_COLOR=0 aw <cmd>"
                or (inv.startswith("FORCE_COLOR=0") and "| cat" not in inv)
                for inv in invoc_texts
            ),
            "Missing required row: 'FORCE_COLOR=0' on a TTY",
        )

        # (e) Report every mismatch at once
        mismatches = []
        for r in rows:
            for k in ("NO_COLOR", "FORCE_COLOR"):
                os.environ.pop(k, None)
            os.environ["TERM"] = "xterm-256color"
            for k, v in r["env"].items():
                os.environ[k] = v
            T.set_color_override(r["override"])
            stream = _FakeTTY() if r["is_tty"] else _FakePipe()
            measured = T.should_color(stream, override=r["override"])
            if measured != r["expected"]:
                mismatches.append(
                    f"Invocation: {r['invoc']!r} | "
                    f"Documented: {'colored' if r['expected'] else 'monochrome'} | "
                    f"Measured: {'colored' if measured else 'monochrome'}"
                )

        if mismatches:
            self.fail(
                "Documented color contract table mismatches:\n" + "\n".join(mismatches)
            )


class ColorPrecedenceTests(unittest.TestCase):
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

    def test_precedence_rungs_flag_beats_env_beats_detection(self):
        # Rung 1: flag beats env
        os.environ["NO_COLOR"] = "1"
        self.assertTrue(T.should_color(_FakeTTY(), override=True))
        self.assertTrue(T.should_color(_FakePipe(), override=True))

        os.environ["FORCE_COLOR"] = "1"
        self.assertFalse(T.should_color(_FakeTTY(), override=False))
        self.assertFalse(T.should_color(_FakePipe(), override=False))

        self.assertFalse(T.should_color(_FakeTTY(), override=False))

        os.environ["TERM"] = "dumb"
        self.assertTrue(T.should_color(_FakeTTY(), override=True))

        # Rung 2: env beats detection without flag
        os.environ["TERM"] = "xterm-256color"
        os.environ["FORCE_COLOR"] = "1"
        self.assertTrue(T.should_color(_FakePipe()))
        os.environ.pop("FORCE_COLOR")
        os.environ["NO_COLOR"] = "1"
        self.assertFalse(T.should_color(_FakeTTY()))

        # Rung 3: detection alone
        os.environ.pop("NO_COLOR", None)
        self.assertTrue(T.should_color(_FakeTTY()))
        self.assertFalse(T.should_color(_FakePipe()))

    def test_process_wide_override_and_namespace(self):
        import argparse as _argparse

        T.set_color_override(True)
        self.assertTrue(T.should_color(_FakePipe()))
        self.assertEqual(T.get_color_override(), True)
        T.set_color_override(None)
        self.assertFalse(T.should_color(_FakePipe()))
        self.assertIsNone(T.get_color_override())

        T.set_color_override(False)
        self.assertTrue(T.should_color(_FakePipe(), override=True))

        before = {k: os.environ.get(k) for k in ("NO_COLOR", "FORCE_COLOR", "TERM")}
        T.set_color_override(True)
        T.should_color(_FakePipe())
        T.set_color_override(False)
        T.should_color(_FakeTTY())
        after = {k: os.environ.get(k) for k in ("NO_COLOR", "FORCE_COLOR", "TERM")}
        self.assertEqual(before, after)

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
        self.assertFalse(
            T.color_override(_argparse.Namespace(no_color=True, color=True))
        )

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
    def test_colorize_and_256_styling(self):
        # Plain vs Color
        t_off = T.Term(stream=io.StringIO(), color=False)
        self.assertEqual(t_off.colorize("hi", "red", "bold"), "hi")
        self.assertEqual(t_off.color256("hi", 39, bold=True), "hi")

        t_on = T.Term(stream=io.StringIO(), color=True)
        out = t_on.colorize("hi", "red")
        self.assertRegex(out, _ANSI)
        self.assertIn("hi", out)

        out256 = t_on.color256("hi", 39)
        self.assertIn("\033[38;5;39m", out256)
        self.assertIn("hi", out256)
        self.assertTrue(out256.endswith("\033[0m"))
        self.assertEqual(_ANSI.sub("", out256), "hi")

        # Bold prefix & Clamping
        self.assertIn("\033[1;38;5;203m", t_on.color256("x", 203, bold=True))
        self.assertIn("38;5;255m", t_on.color256("x", 999))
        self.assertIn("38;5;0m", t_on.color256("x", -5))

        # Status word presence
        s_off = io.StringIO()
        T.Term(stream=s_off, color=False).status("fail", "something broke")
        self.assertNotRegex(s_off.getvalue(), _ANSI)
        self.assertIn("FAIL", s_off.getvalue())
        self.assertIn("something broke", s_off.getvalue())

        s_on = io.StringIO()
        T.Term(stream=s_on, color=True).status("ok", "done")
        self.assertIn("OK", _ANSI.sub("", s_on.getvalue()))

        # status_256
        out_s256 = t_on.status_256("updated", width=12)
        self.assertIn("\033[1;38;5;46mupdated\033[0m", out_s256)
        self.assertEqual(len(_ANSI.sub("", out_s256)), 12)
        out_s256_plain = t_off.status_256("updated", width=12)
        self.assertEqual(out_s256_plain, "updated     ")

        for lifecycle_status in (
            "open",
            "approved",
            "executed",
            "draft",
            "implementing",
        ):
            with self.subTest(status=lifecycle_status):
                self.assertNotIn(lifecycle_status, T.ROLE_COLOR_256)
                self.assertIn("\033[1;38;5;244m", t_on.status_256(lifecycle_status))

    def test_attention_shared_lifecycle_integration(self):
        from agent_workflows import attention as att
        from agent_workflows import attention_contract as A

        self.assertFalse(hasattr(att, "_STATUS_COLOR_256"))
        self.assertTrue(hasattr(att, "_CLASS_COLOR_256"))
        self.assertEqual(
            set(att._CLASS_COLOR_256),
            {A.ACTIVE, A.READY, A.BLOCKED, A.DONE, A.PARKED},
        )

        item = att.Item(
            "aaa111",
            ".aw/records/backlog/open/x.backlog.md",
            "backlog",
            "open",
            A.READY,
            None,
            "2026-05-01",
        )
        out = att.render_board(
            [item], [], show_all=True, term=T.Term(stream=io.StringIO(), color=True)
        )
        expected = LS.resolve(LS.FAMILY_BACKLOG, "open")
        self.assertEqual(expected.stage, LS.READY)
        self.assertIn(f"\033[1;38;5;{expected.style.color}mopen\033[0m", out)


class CliNeverLeaksTheColorOverrideTests(unittest.TestCase):
    def setUp(self):
        self._saved = {
            k: os.environ.get(k) for k in ("NO_COLOR", "FORCE_COLOR", "TERM")
        }
        self.addCleanup(self._restore)
        self.addCleanup(T.set_color_override, None)
        for k in ("NO_COLOR", "FORCE_COLOR"):
            os.environ.pop(k, None)
        os.environ["TERM"] = "xterm-256color"
        T.set_color_override(None)

    def _restore(self):
        for k, v in self._saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    EARLY_EXIT_PATHS = (
        ("--no-color then a subcommand --help", ["--no-color", "check", "--help"]),
        ("--color then a subcommand --help", ["--color", "check", "--help"]),
        ("--no-color then top-level --help", ["--no-color", "--help"]),
        ("--no-color then an unknown verb", ["--no-color", "definitely-not-a-verb"]),
        ("--color with no verb at all", ["--color"]),
    )

    def test_early_exit_paths_and_nested_invocations(self):
        class _TTY(io.StringIO):
            def isatty(self):
                return True

        for case, argv in self.EARLY_EXIT_PATHS:
            with self.subTest(case=case):
                T.set_color_override(None)
                buf = io.StringIO()
                try:
                    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(
                        buf
                    ):
                        cli.main(list(argv))
                except SystemExit:
                    pass
                self.assertIsNone(T.get_color_override(), f"Override leaked in {case}")
                self.assertTrue(
                    T.should_color(_TTY()), f"TTY should_color broken after {case}"
                )

        # Nested invocation preserves outer override
        T.set_color_override(True)
        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
                cli.main(["check", "--help"])
        except SystemExit:
            pass
        self.assertIs(T.get_color_override(), True)


class CliNeverLeaksTheInteractivityOverrideTests(unittest.TestCase):
    """svqhmp bmf32u E-03 / V-03: Process-wide interactivity override never leaks across invocations."""

    def setUp(self):
        self._saved_override = T.get_interactive_override()
        self.addCleanup(T.set_interactive_override, self._saved_override)
        T.set_interactive_override(None)

    EARLY_EXIT_PATHS = (
        (
            "--no-interactive then a subcommand --help",
            ["--no-interactive", "check", "--help"],
        ),
        (
            "--interactive then a subcommand --help",
            ["--interactive", "check", "--help"],
        ),
        ("--no-interactive then top-level --help", ["--no-interactive", "--help"]),
        (
            "--no-interactive then an unknown verb",
            ["--no-interactive", "definitely-not-a-verb"],
        ),
        ("--interactive with no verb at all", ["--interactive"]),
    )

    def test_early_exit_paths_and_nested_invocations(self):
        class _TTY(io.StringIO):
            def isatty(self):
                return True

        for case, argv in self.EARLY_EXIT_PATHS:
            with self.subTest(case=case):
                T.set_interactive_override(None)
                buf = io.StringIO()
                try:
                    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(
                        buf
                    ):
                        cli.main(list(argv))
                except SystemExit:
                    pass
                self.assertIsNone(
                    T.get_interactive_override(), f"Override leaked in {case}"
                )
                self.assertTrue(
                    T.is_interactive(stdin=_TTY(), output_stream=_TTY(), environ={}),
                    f"TTY is_interactive broken after {case}",
                )

        # Flagless invocation resets a previously set process-wide override
        T.set_interactive_override(True)
        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
                cli.main(["check", "--help"])
        except SystemExit:
            pass
        self.assertIs(
            T.get_interactive_override(),
            True,
            "Outer override must survive nested invocation",
        )

        # Nested invocation: an outer override is restored after an inner cli.main call
        T.set_interactive_override(False)
        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
                cli.main(["--interactive", "check", "--help"])
        except SystemExit:
            pass
        self.assertIs(
            T.get_interactive_override(),
            False,
            "Outer False override must survive inner --interactive call",
        )


class InteractivityAndColorIndependenceTests(unittest.TestCase):
    """svqhmp bmf32u E-05 / V-05: 2x2 matrix proving presentation and interactivity axes stay independent."""

    def setUp(self):
        self._orig_color = T.get_color_override()
        self._orig_interactive = T.get_interactive_override()
        self.addCleanup(T.set_color_override, self._orig_color)
        self.addCleanup(T.set_interactive_override, self._orig_interactive)
        T.set_color_override(None)
        T.set_interactive_override(None)

    def test_2x2_independence_matrix(self):
        class _TTY(io.StringIO):
            def isatty(self):
                return True

        class _Pipe(io.StringIO):
            def isatty(self):
                return False

        tty = _TTY()
        pipe = _Pipe()

        # Base values with no override
        base_i_tty = T.is_interactive(stdin=tty, output_stream=tty, environ={})
        base_i_pipe = T.is_interactive(stdin=pipe, output_stream=pipe, environ={})
        base_c_tty = T.should_color(tty)
        base_c_pipe = T.should_color(pipe)

        # 1 & 2: Color overrides (--color, --no-color) do NOT alter interactivity answers
        for color_val, label in ((True, "--color"), (False, "--no-color")):
            with self.subTest(color=label):
                T.set_color_override(color_val)
                self.assertEqual(
                    T.is_interactive(stdin=tty, output_stream=tty, environ={}),
                    base_i_tty,
                    f"{label} altered interactivity answer on TTY",
                )
                self.assertEqual(
                    T.is_interactive(stdin=pipe, output_stream=pipe, environ={}),
                    base_i_pipe,
                    f"{label} altered interactivity answer on pipe",
                )
        T.set_color_override(None)

        # 3 & 4: Interactivity overrides (--interactive, --no-interactive) do NOT alter color answers
        for inter_val, label in ((True, "--interactive"), (False, "--no-interactive")):
            with self.subTest(interactive=label):
                T.set_interactive_override(inter_val)
                self.assertEqual(
                    T.should_color(tty),
                    base_c_tty,
                    f"{label} altered should_color answer on TTY",
                )
                self.assertEqual(
                    T.should_color(pipe),
                    base_c_pipe,
                    f"{label} altered should_color answer on pipe",
                )
        T.set_interactive_override(None)


class _DepthTestBase(unittest.TestCase):
    def setUp(self):
        self._saved = {
            k: os.environ.get(k)
            for k in ("NO_COLOR", "FORCE_COLOR", "TERM", "COLORTERM", "XDG_CONFIG_HOME")
        }
        self._tmp = tempfile.TemporaryDirectory()
        os.environ["XDG_CONFIG_HOME"] = self._tmp.name
        self.addCleanup(self._tmp.cleanup)
        self.addCleanup(self._restore_env)
        self.addCleanup(T.set_color_override, None)

    def _restore_env(self):
        for k, v in self._saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    def _capable_tty(self):
        for k in ("NO_COLOR", "FORCE_COLOR", "COLORTERM"):
            os.environ.pop(k, None)
        os.environ["TERM"] = "xterm-256color"
        T.set_color_override(None)
        cfg = CFG.load()
        if "color_depth" in cfg:
            cfg.pop("color_depth")
            CFG.save(cfg)

    def _pin(self, value):
        CFG.set_config_value("color_depth", value)


class ColorDepthPrecedenceTests(_DepthTestBase):
    def test_rung1_color_off_and_accessibility_convention(self):
        self._capable_tty()
        os.environ["NO_COLOR"] = "1"
        self.assertEqual(T.resolve_color_depth(_FakeTTY()), T.DEPTH_NONE)

        self._capable_tty()
        os.environ["TERM"] = "dumb"
        self.assertEqual(T.resolve_color_depth(_FakeTTY()), T.DEPTH_NONE)

        self._capable_tty()
        self.assertEqual(T.resolve_color_depth(_FakePipe()), T.DEPTH_NONE)

        self._capable_tty()
        self.assertEqual(
            T.resolve_color_depth(_FakeTTY(), override=False), T.DEPTH_NONE
        )

        self._capable_tty()
        T.set_color_override(False)
        self.assertEqual(T.resolve_color_depth(_FakeTTY()), T.DEPTH_NONE)

        # NO_COLOR beats pinned depth
        self._capable_tty()
        self._pin("256")
        os.environ["NO_COLOR"] = "1"
        self.assertEqual(T.resolve_color_depth(_FakeTTY()), T.DEPTH_NONE)

        self._capable_tty()
        self._pin("16")
        os.environ["NO_COLOR"] = "1"
        self.assertEqual(T.resolve_color_depth(_FakeTTY()), T.DEPTH_NONE)

        # FORCE_COLOR overrides NO_COLOR
        self._capable_tty()
        os.environ["NO_COLOR"] = "1"
        os.environ["FORCE_COLOR"] = "1"
        self.assertEqual(T.resolve_color_depth(_FakePipe()), T.DEPTH_256)

    def test_rung2_pinned_depth_overrides_detection(self):
        self._capable_tty()
        self._pin("16")
        self.assertEqual(T.resolve_color_depth(_FakeTTY()), T.DEPTH_16)

        self._capable_tty()
        self._pin("none")
        self.assertEqual(T.resolve_color_depth(_FakeTTY()), T.DEPTH_NONE)

        self._capable_tty()
        os.environ["TERM"] = "xterm-16color"
        self._pin("256")
        self.assertEqual(T.resolve_color_depth(_FakeTTY()), T.DEPTH_256)

    def test_rung3_and_rung4_detection_and_defaults(self):
        self._capable_tty()
        os.environ["TERM"] = "xterm-16color"
        self.assertEqual(T.resolve_color_depth(_FakeTTY()), T.DEPTH_16)

        self._capable_tty()
        self.assertEqual(T.resolve_color_depth(_FakeTTY()), T.DEPTH_256)

        self._capable_tty()
        os.environ["TERM"] = "sometermnobodyknows"
        os.environ["COLORTERM"] = "truecolor"
        self.assertEqual(T.resolve_color_depth(_FakeTTY()), T.DEPTH_256)

        self._capable_tty()
        os.environ["TERM"] = "linux"
        self.assertEqual(T.resolve_color_depth(_FakeTTY()), T.DEPTH_16)

        self._capable_tty()
        os.environ["TERM"] = "sometermnobodyknows"
        self.assertEqual(T.resolve_color_depth(_FakeTTY()), T.DEPTH_256)
        self.assertEqual(T.DEFAULT_COLOR_DEPTH, T.DEPTH_256)

        # Invalid pin in config falls through
        self._capable_tty()
        cfg = CFG.load()
        cfg["color_depth"] = "tru3color"
        CFG.save(cfg)
        self.assertEqual(T.resolve_color_depth(_FakeTTY()), T.DEPTH_256)


class AuthoredSixteenColorPaletteTests(unittest.TestCase):
    def test_palette_coverage_named_colors_separations_and_collapses(self):
        self.assertEqual(set(T.STAGE_COLOR_16), set(LS.ALL_STAGES))

        named = set(range(30, 38)) | set(range(90, 98))
        wrong = {s: c for s, c in T.STAGE_COLOR_16.items() if c not in named}
        self.assertEqual(wrong, {})

        # Separations
        self.assertNotEqual(T.color_16_for_stage("ready"), T.color_16_for_stage("done"))
        self.assertNotEqual(
            T.color_16_for_stage("blocked"), T.color_16_for_stage("failed")
        )
        self.assertNotEqual(
            T.color_16_for_stage("waiting-input"), T.color_16_for_stage("blocked")
        )
        for left, right in T.REQUIRED_16_COLOR_SEPARATIONS:
            self.assertNotEqual(T.color_16_for_stage(left), T.color_16_for_stage(right))

        # Collapses
        active_group = (
            "reviewing",
            "executing",
            "verifying",
            "integrating",
            "recovering",
            "active",
        )
        self.assertEqual(len({T.color_16_for_stage(s) for s in active_group}), 1)

        gray_group = (
            "parked",
            "superseded",
            "abandoned",
            "unknown",
            "none",
            "formative",
        )
        self.assertEqual(len({T.color_16_for_stage(s) for s in gray_group}), 1)

        # No unnamed merges
        collapse_members = {s for group in T.EXPECTED_16_COLOR_COLLAPSES for s in group}
        by_code = {}
        for stage, code in T.STAGE_COLOR_16.items():
            by_code.setdefault(code, []).append(stage)
        offenders = {
            code: sorted(s for s in stages if s not in collapse_members)
            for code, stages in by_code.items()
            if len([s for s in stages if s not in collapse_members]) > 1
        }
        self.assertEqual(offenders, {})

    def test_validator_rejects_corrupted_palettes(self):
        from unittest import mock

        broken = dict(T.STAGE_COLOR_16)
        broken["authority-queued"] = broken["blocked"]
        with mock.patch.object(T, "STAGE_COLOR_16", broken):
            with self.assertRaises(ValueError):
                T.validate_16_color_palette()

        broken = dict(T.STAGE_COLOR_16)
        broken["blocked"] = broken["failed"]
        with mock.patch.object(T, "STAGE_COLOR_16", broken):
            with self.assertRaises(ValueError):
                T.validate_16_color_palette()

        broken = dict(T.STAGE_COLOR_16)
        broken.pop("ready")
        with mock.patch.object(T, "STAGE_COLOR_16", broken):
            with self.assertRaises(ValueError):
                T.validate_16_color_palette()

        broken = dict(T.STAGE_COLOR_16)
        broken["verifying"] = 34
        with mock.patch.object(T, "STAGE_COLOR_16", broken):
            with self.assertRaises(ValueError):
                T.validate_16_color_palette()


class EveryTierKeepsTheInvariantTests(_DepthTestBase):
    FIXTURE = (
        ("plans", "approved"),
        ("plans", "executed"),
        ("backlog", "blocked"),
        ("runner-item", "failed"),
        ("runner-item", "needs_input"),
        ("specs", "implementing"),
        ("specs", "parked"),
    )

    def _render(self, tier):
        rows = []
        for family, native in self.FIXTURE:
            resolved = LS.resolve(family, native)
            glyph = resolved.style.unicode
            if tier == T.DEPTH_256:
                painted = f"\033[38;5;{resolved.style.color}m{glyph}\033[0m"
            elif tier == T.DEPTH_16:
                painted = f"\033[{T.color_16_for_stage(resolved.stage)}m{glyph}\033[0m"
            else:
                painted = glyph
            rows.append((resolved.stage, native, f"{painted} {native}"))
        return rows

    def test_invariant_glyph_and_word_preserved_across_tiers(self):
        for tier in (T.DEPTH_256, T.DEPTH_16, T.DEPTH_NONE):
            rows = self._render(tier)
            for stage, native, line in rows:
                plain = T.strip_ansi(line)
                self.assertIn(native, plain)
                self.assertIn(LS.STAGES[stage].unicode, plain)

            for i, (stage_a, _, line_a) in enumerate(rows):
                for stage_b, _, line_b in rows[i + 1 :]:
                    if stage_a != stage_b:
                        self.assertNotEqual(T.strip_ansi(line_a), T.strip_ansi(line_b))

            if tier == T.DEPTH_NONE:
                for _, _, line in rows:
                    self.assertEqual(line, T.strip_ansi(line))
            else:
                for _, _, line in rows:
                    self.assertNotEqual(line, T.strip_ansi(line))

        for group in T.EXPECTED_16_COLOR_COLLAPSES:
            glyphs = {LS.STAGES[stage].unicode for stage in group}
            shared_color = {T.color_16_for_stage(stage) for stage in group}
            self.assertEqual(len(shared_color), 1)
            self.assertEqual(len(glyphs), len(group))


class ColorDepthConfigContractTests(_DepthTestBase):
    def test_config_enum_matches_resolver(self):
        self.assertEqual(tuple(CFG.COLOR_DEPTH_VALUES), tuple(T.COLOR_DEPTHS))
        self._capable_tty()
        for value in CFG.COLOR_DEPTH_VALUES:
            with self.subTest(pin=value):
                self._pin(value)
                self.assertEqual(T.resolve_color_depth(_FakeTTY()), value)


_VS_BLOCKED = "\u26a0\ufe0e"
_VS_RECOVERING = "\u21a9\ufe0e"
_NO_VS_READY = "\u25d5"


class ResolutionIsSeparateFromRenderingTests(unittest.TestCase):
    def test_resolution_is_pure_data_and_deterministic(self):
        resolved = T.resolve_lifecycle("backlog", "blocked")
        self.assertNotIn("\033", repr(resolved))
        self.assertEqual(resolved.stage, LS.BLOCKED)
        self.assertEqual(resolved.native_status, "blocked")

        # Independent of environment
        saved = {k: os.environ.get(k) for k in ("NO_COLOR", "FORCE_COLOR", "TERM")}
        try:
            answers = []
            for env in (
                {"TERM": "xterm-256color"},
                {"NO_COLOR": "1", "TERM": "dumb"},
                {"FORCE_COLOR": "1", "TERM": ""},
            ):
                for k in ("NO_COLOR", "FORCE_COLOR", "TERM"):
                    os.environ.pop(k, None)
                os.environ.update(env)
                answers.append(repr(T.resolve_lifecycle("plans", "approved")))
            self.assertEqual(len(set(answers)), 1)
        finally:
            for k, v in saved.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v

        for res in (
            T.resolve_lifecycle("plans", "approved"),
            T.resolve_lifecycle("plans", "approved", activity="executing"),
            T.resolve_lifecycle("releases", "planned"),
        ):
            self.assertTrue(T.lifecycle_word(res).strip())

        res_case = T.resolve_lifecycle("specs", "Implementing")
        self.assertEqual(T.lifecycle_word(res_case), "Implementing")
        self.assertEqual(res_case.stage, LS.EXECUTING)

    def test_term_delegates_to_lifecycle_style(self):
        for mode in (True, False):
            term = T.Term(color=False, unicode=mode)
            for stage in LS.STAGE_ORDER:
                style = LS.style_for(stage)
                resolved = LS.Resolved(stage=stage, style=style, family=LS.FAMILY_PLANS)
                with self.subTest(stage=stage, unicode=mode):
                    self.assertEqual(
                        term.format_lifecycle_marker(resolved),
                        style.unicode if mode else style.ascii,
                    )


class FullRowStylingTests(unittest.TestCase):
    def setUp(self):
        self.term = T.Term(color=True, unicode=True, depth=T.DEPTH_256)
        self.resolved = T.resolve_lifecycle("backlog", "blocked")

    def _row(self, **kwargs):
        return self.term.format_lifecycle_row(self.resolved, **kwargs)

    def test_lifecycle_row_styling(self):
        row = self._row(
            id6="abc123", artifact_type="BACKLOG", title="Short title", path="a/b.md"
        )
        codes = _ANSI.findall(row)
        opens = [c for c in codes if c != "\033[0m"]
        self.assertEqual(len(opens), 3)
        self.assertEqual(len(set(opens)), 1)
        expected = f"\033[1;38;5;{LS.style_for(LS.BLOCKED).color}m"
        self.assertEqual(opens[0], expected)

        for neutral in ("BACKLOG", "Short title", "a/b.md"):
            idx = row.index(neutral)
            self.assertNotIn("\033", row[idx : idx + len(neutral)])

        # No whole row coloring parameter in signature
        params = set(inspect.signature(T.Term.format_lifecycle_row).parameters)
        for forbidden in (
            "style_title",
            "style_type",
            "style_path",
            "style_row",
            "whole_row",
            "color_row",
        ):
            self.assertNotIn(forbidden, params)

        # Unbolded stage
        res_draft = T.resolve_lifecycle("plans", "draft")
        row_draft = self.term.format_lifecycle_row(res_draft, id6="abc123")
        self.assertIn(f"\033[38;5;{res_draft.style.color}m", row_draft)
        self.assertNotIn("\033[1;", row_draft)

        # Glyph precedes id6
        plain = T.strip_ansi(self._row(id6="abc123", artifact_type="BACKLOG"))
        self.assertRegex(plain, r"\u26a0\ufe0e\s+abc123")

        # Visible width invariant
        blocked = self.term.format_lifecycle_row(
            T.resolve_lifecycle("backlog", "blocked"),
            id6="abc123",
            status_width=12,
            marker_width=3,
        )
        ready = self.term.format_lifecycle_row(
            T.resolve_lifecycle("plans", "approved"),
            id6="abc123",
            status_width=12,
            marker_width=3,
        )
        self.assertEqual(
            T.visible_width(blocked.split("abc123")[0]),
            T.visible_width(ready.split("abc123")[0]),
        )


class CompactFormAndLegendTests(unittest.TestCase):
    def setUp(self):
        self.term = T.Term(color=True, unicode=True, depth=T.DEPTH_256)

    def test_lifecycle_compact_and_legend(self):
        resolved = T.resolve_lifecycle("backlog", "blocked")
        out = self.term.format_lifecycle_compact("abc123", resolved)
        expected = f"\033[1;38;5;208m{_VS_BLOCKED}\033[0m \033[1;38;5;208mabc123\033[0m"
        self.assertEqual(out, expected)

        plain = T.Term(color=False, unicode=True)
        seen = {
            plain.format_lifecycle_compact("abc123", T.resolve_lifecycle(f, s))
            for f, s in (
                ("plans", "approved"),
                ("plans", "executed"),
                ("backlog", "blocked"),
            )
        }
        self.assertEqual(len(seen), 3)

        # Legend covers all stages
        lines = self.term.format_lifecycle_legend().splitlines()
        self.assertEqual(len(lines), len(LS.STAGE_ORDER))
        for stage in LS.STAGE_ORDER:
            self.assertTrue(any(line.endswith(stage) for line in lines))

        lines_plain = T.strip_ansi(plain.format_lifecycle_legend()).splitlines()
        self.assertEqual(
            [line.split()[-1] for line in lines_plain], list(LS.STAGE_ORDER)
        )

        # ASCII mode
        lines_ascii = (
            T.Term(color=False, unicode=False).format_lifecycle_legend().splitlines()
        )
        self.assertEqual(len(lines_ascii), len(LS.STAGE_ORDER))
        for stage, line in zip(LS.STAGE_ORDER, lines_ascii):
            style = LS.style_for(stage)
            self.assertTrue(line.startswith(style.ascii))
            self.assertTrue(line.isascii())
            self.assertTrue(line.endswith(stage))

        # Idempotent (no once-per-process latch)
        first = self.term.format_lifecycle_legend()
        self.assertEqual(first, self.term.format_lifecycle_legend())


class GraphemeSafetyTests(unittest.TestCase):
    def test_grapheme_width_variation_selectors_and_ansi(self):
        for glyph in (_VS_BLOCKED, _VS_RECOVERING):
            self.assertEqual(len(glyph), 2)
            self.assertEqual(T.visible_width(glyph), 1)
        self.assertEqual(T.visible_width(_NO_VS_READY), 1)

        for glyph in LS.MULTI_CODEPOINT_GLYPHS:
            self.assertGreater(len(glyph), 1)
            self.assertEqual(T.visible_width(glyph), 1)

        term = T.Term(color=True, unicode=True, depth=T.DEPTH_256)
        styled = term.style_lifecycle_text(
            _VS_BLOCKED, T.resolve_lifecycle("backlog", "blocked")
        )
        self.assertIn("\033", styled)
        self.assertEqual(T.visible_width(styled), T.visible_width(_VS_BLOCKED))

        term_plain = T.Term(color=False, unicode=True)
        widths = {
            stage: T.visible_width(
                term_plain.format_lifecycle_marker(
                    LS.Resolved(
                        stage=stage, style=LS.style_for(stage), family=LS.FAMILY_PLANS
                    ),
                    width=4,
                )
            )
            for stage in LS.STAGE_ORDER
        }
        self.assertEqual(set(widths.values()), {4})

    def test_visible_truncation_safety(self):
        text = "xxx" + _VS_BLOCKED + "tail"
        for limit in range(1, T.visible_width(text) + 1):
            out = T.truncate_visible(text, limit)
            if "\u26a0" in out:
                self.assertIn("\ufe0e", out)

        term = T.Term(color=True, unicode=True, depth=T.DEPTH_256)
        row = term.format_lifecycle_row(
            T.resolve_lifecycle("backlog", "blocked"),
            id6="abc123",
            artifact_type="BACKLOG",
            title="Short title",
        )
        for limit in range(1, T.visible_width(row) + 1):
            out = T.truncate_visible(row, limit)
            if "\u26a0" in out:
                self.assertIn("\ufe0e", out)
            self.assertLessEqual(T.visible_width(out), limit)

        row_styled_open = term.format_lifecycle_row(
            T.resolve_lifecycle("backlog", "blocked"), id6="abc123"
        )
        out_closed = T.truncate_visible(row_styled_open, 4)
        self.assertTrue(out_closed.endswith("\033[0m"))
        self.assertEqual(T.truncate_visible(row, 500), row)

        out_ellipsis = T.truncate_visible(row, 12, ellipsis="\u2026")
        self.assertLessEqual(T.visible_width(out_ellipsis), 12)
        self.assertTrue(out_ellipsis.endswith("\u2026"))
        self.assertFalse(out_ellipsis.endswith("\u2026\033[0m"))

    def test_encoding_safety_ascii_and_presentation(self):
        term = T.Term(color=False, unicode=False)
        for stage in LS.STAGE_ORDER:
            resolved = LS.Resolved(
                stage=stage, style=LS.style_for(stage), family=LS.FAMILY_PLANS
            )
            rendered = term.format_lifecycle_marker(resolved)
            self.assertTrue(rendered.isascii())
            self.assertEqual(len(rendered.encode("ascii")), 1)

        for mode in (True, False):
            term_pad = T.Term(color=False, unicode=mode)
            for stage in LS.STAGE_ORDER:
                resolved = LS.Resolved(
                    stage=stage, style=LS.style_for(stage), family=LS.FAMILY_PLANS
                )
                self.assertEqual(
                    T.visible_width(
                        term_pad.format_lifecycle_marker(resolved, width=6)
                    ),
                    6,
                )

        term_styled = T.Term(color=True, unicode=True, depth=T.DEPTH_256)
        styled = term_styled.format_lifecycle_marker(
            T.resolve_lifecycle("backlog", "blocked")
        )
        self.assertIn("\ufe0e", T.strip_ansi(styled))

        for tier in (T.DEPTH_256, T.DEPTH_16, T.DEPTH_NONE):
            for mode in (True, False):
                term_e = T.Term(color=tier != T.DEPTH_NONE, unicode=mode, depth=tier)
                self.assertNotIn("\ufe0f", term_e.format_lifecycle_legend())


class CapabilityMatrixTests(unittest.TestCase):
    FAMILY, NATIVE, STAGE = "backlog", "blocked", LS.BLOCKED

    def setUp(self):
        self._saved = {
            k: os.environ.get(k)
            for k in (
                "NO_COLOR",
                "FORCE_COLOR",
                "TERM",
                "COLORTERM",
                "AW_ASCII_ONLY",
                "FORCE_ASCII",
                "XDG_CONFIG_HOME",
            )
        }
        self._tmp = tempfile.TemporaryDirectory()
        os.environ["XDG_CONFIG_HOME"] = self._tmp.name
        self.addCleanup(self._tmp.cleanup)
        self.addCleanup(self._restore)
        self.addCleanup(T.set_color_override, None)
        for k in (
            "NO_COLOR",
            "FORCE_COLOR",
            "COLORTERM",
            "AW_ASCII_ONLY",
            "FORCE_ASCII",
        ):
            os.environ.pop(k, None)
        os.environ["TERM"] = "xterm-256color"

    def _restore(self):
        for k, v in self._saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    def _render(self, stream):
        term = T.Term(stream)
        resolved = T.resolve_lifecycle(self.FAMILY, self.NATIVE)
        return term.format_lifecycle_row(
            resolved, id6="abc123", artifact_type="BACKLOG"
        )

    def _assert_profile(self, out, *, ansi, unicode_form):
        style = LS.style_for(self.STAGE)
        if ansi:
            self.assertIn("\033[", out)
        else:
            self.assertNotIn("\033", out)
        plain = T.strip_ansi(out)
        if unicode_form:
            self.assertIn(style.unicode, plain)
        else:
            self.assertNotIn(style.unicode, plain)
            self.assertIn(style.ascii, plain)
        self.assertIn(self.NATIVE, plain)

    def test_standard_profiles_1_to_6(self):
        # Profile 1: normal utf8
        self._assert_profile(self._render(_Utf8TTY()), ansi=True, unicode_form=True)

        # Profile 2: ascii mode
        os.environ["AW_ASCII_ONLY"] = "1"
        self._assert_profile(self._render(_Utf8TTY()), ansi=True, unicode_form=False)
        os.environ.pop("AW_ASCII_ONLY")

        # Profile 2b: force ascii
        os.environ["FORCE_ASCII"] = "1"
        self._assert_profile(self._render(_Utf8TTY()), ansi=True, unicode_form=False)
        os.environ.pop("FORCE_ASCII")

        # Profile 3: colored tty
        os.environ["TERM"] = "xterm-256color"
        out3 = self._render(_Utf8TTY())
        self._assert_profile(out3, ansi=True, unicode_form=True)
        self.assertIn(f"38;5;{LS.style_for(self.STAGE).color}", out3)

        # Profile 4: plain tty
        os.environ["NO_COLOR"] = "1"
        self._assert_profile(self._render(_Utf8TTY()), ansi=False, unicode_form=True)
        os.environ.pop("NO_COLOR")

        # Profile 5: piped output
        self._assert_profile(self._render(_Utf8Pipe()), ansi=False, unicode_form=True)

        # Profile 6: term dumb
        os.environ["TERM"] = "dumb"
        self._assert_profile(self._render(_Utf8TTY()), ansi=False, unicode_form=True)

    def test_force_color_and_16_color_profiles(self):
        # FORCE_COLOR enables ansi on pipe
        os.environ["FORCE_COLOR"] = "1"
        self._assert_profile(self._render(_Utf8Pipe()), ansi=True, unicode_form=True)

        # FORCE_COLOR does not force unicode onto ascii stream
        out_ascii = self._render(_AsciiPipe())
        self._assert_profile(out_ascii, ansi=True, unicode_form=False)

        # NO_COLOR flag beats FORCE_COLOR
        T.set_color_override(False)
        self._assert_profile(self._render(_Utf8TTY()), ansi=False, unicode_form=True)
        T.set_color_override(None)

        # Falsey FORCE_COLOR
        os.environ["FORCE_COLOR"] = "0"
        self._assert_profile(self._render(_Utf8Pipe()), ansi=False, unicode_form=True)

        # 16-color tier rendering
        os.environ.pop("FORCE_COLOR")
        os.environ["TERM"] = "xterm-color"
        out16 = self._render(_Utf8TTY())
        self.assertIn(f"\033[1;{T.color_16_for_stage(self.STAGE)}m", out16)
        self.assertNotIn("38;5;", out16)


class ColorDepthEndToEndLadderTests(unittest.TestCase):
    """End-to-end color depth ladder tests asserting on observable ANSI bytes (E-04)."""

    def test_end_to_end_ladder_observable_ansi_rendering(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            env = os.environ.copy()
            env["XDG_CONFIG_HOME"] = tmpdir
            env["AW_NO_REEXEC"] = "1"
            env["TERM"] = "xterm-256color"
            env.pop("NO_COLOR", None)
            env.pop("FORCE_COLOR", None)
            env.pop("COLORTERM", None)

            def _pin(tier: str) -> None:
                subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "agent_workflows",
                        "config",
                        "set",
                        "color_depth",
                        tier,
                    ],
                    env=env,
                    check=True,
                    capture_output=True,
                )

            def _find_backlog(*args: str) -> subprocess.CompletedProcess[str]:
                return subprocess.run(
                    [sys.executable, "-m", "agent_workflows", "find", "backlog", *args],
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    check=True,
                )

            # Cell 1: --color and pin 256 -> some escape code contains 38;5;
            _pin("256")
            res_256 = _find_backlog("--color")
            escapes_256 = re.findall(r"\033\[([0-9;]*)m", res_256.stdout)
            self.assertTrue(
                any("38;5;" in code for code in escapes_256),
                f"Expected 38;5; escape in 256 pin output, got: {escapes_256}",
            )

            # Cell 2: --color and pin 16 -> NO code contains 38;5;
            _pin("16")
            res_16 = _find_backlog("--color")
            escapes_16 = re.findall(r"\033\[([0-9;]*)m", res_16.stdout)
            self.assertTrue(
                len(escapes_16) > 0, "Expected ANSI escapes for 16-color pin"
            )
            self.assertFalse(
                any("38;5;" in code for code in escapes_16),
                f"Expected no 38;5; escape in 16 pin output, got: {escapes_16}",
            )

            # Cell 3: --color and pin none -> stdout contains NO \x1b at all (regression gate)
            _pin("none")
            res_none = _find_backlog("--color")
            self.assertNotIn(
                "\033",
                res_none.stdout,
                "Expected no ANSI escapes at color_depth=none even with --color",
            )

            # Cell 4: NO flag on a pipe -> stdout contains no \x1b regardless of pin (criterion A11)
            for tier in ("256", "16", "none"):
                _pin(tier)
                res_noflag = _find_backlog()
                self.assertNotIn(
                    "\033",
                    res_noflag.stdout,
                    f"Expected no ANSI escapes without --color on pipe at pin={tier}",
                )


class LifecycleDepthConsumerTests(_DepthTestBase):
    """Direct behavioral tests for the Term.lifecycle_depth consumer and agreement (E-05)."""

    def test_lifecycle_depth_consumer_and_two_consumer_agreement(self):
        resolved = T.resolve_lifecycle("backlog", "blocked")

        # Cell (a): pin none -> lifecycle_depth == DEPTH_NONE and style_lifecycle_text bare word with no \x1b
        self._capable_tty()
        self._pin("none")
        t_none = T.Term(stream=_FakeTTY())
        self.assertEqual(t_none.lifecycle_depth(), T.DEPTH_NONE)
        styled_none = t_none.style_lifecycle_text("blocked", resolved)
        self.assertEqual(styled_none, "blocked")
        self.assertNotIn("\033", styled_none)

        # Cell (b): pin 16 -> DEPTH_16 and styled text contains no 38;5;
        self._capable_tty()
        self._pin("16")
        t_16 = T.Term(stream=_FakeTTY())
        self.assertEqual(t_16.lifecycle_depth(), T.DEPTH_16)
        styled_16 = t_16.style_lifecycle_text("blocked", resolved)
        self.assertIn("\033", styled_16)
        self.assertNotIn("38;5;", styled_16)

        # Cell (c): pin 256 -> DEPTH_256
        self._capable_tty()
        self._pin("256")
        t_256 = T.Term(stream=_FakeTTY())
        self.assertEqual(t_256.lifecycle_depth(), T.DEPTH_256)

        # Cell (d): override=True guard cell: Term(stream=<fake pipe>, color=True) with pin 16 resolves 16.
        # Without override=True, the naive fix returns 'none'; the shipped code returns '256'.
        self._capable_tty()
        self._pin("16")
        t_pipe_16 = T.Term(stream=_FakePipe(), color=True)
        self.assertEqual(t_pipe_16.lifecycle_depth(), T.DEPTH_16)

        # Two-consumer agreement across all three pins:
        # Palette(True).lifecycle(resolved) and Term(stream=<fake TTY>).style_lifecycle_text("blocked", resolved)
        # must agree everywhere.
        for pin in (T.DEPTH_NONE, T.DEPTH_16, T.DEPTH_256):
            with self.subTest(pin=pin):
                self._capable_tty()
                self._pin(pin)
                pal = render_stream.Palette(True)
                t_term = T.Term(stream=_FakeTTY())
                self.assertEqual(
                    t_term.style_lifecycle_text("blocked", resolved),
                    pal.lifecycle(resolved),
                )


class LifecycleColorDepthSeamSweepTests(_DepthTestBase):
    """Guard the 256/16/none lifecycle color-depth ladder across all rendering seams (E-03).

    Residual exposure and limits (E-05):
    1. Covers the LIFECYCLE axis only: the generic color axis (colorize, color256,
       status_256, badge, format_path) ignores the depth pin entirely per finding F-08,
       tracked in carrier backlog item cvtg9u.
    2. Proves the five enumerated public rendering seams across all stages, tiers, and
       streams, but does not mechanically prevent a future renderer from re-deriving or
       coercing a tier; it catches a re-collapse by asserting on returned byte output
       at breadth rather than by inspecting code structure (per maintainer ruling p5qx91).
    3. The ladder is CAUGHT, not structurally PREVENTED.
    """

    def test_seam_sweep_across_all_stages_tiers_and_streams(self):
        stages = LS.ALL_STAGES
        tiers = T.COLOR_DEPTHS
        streams = (
            ("tty", lambda: (T.Term(stream=_FakeTTY()), render_stream.Palette(True))),
            (
                "pipe",
                lambda: (
                    T.Term(stream=_FakePipe(), color=True),
                    render_stream.Palette(True),
                ),
            ),
        )

        failures: list[str] = []
        total_cells = 0
        total_seam_evaluations = 0

        for tier in tiers:
            self._capable_tty()
            self._pin(tier)
            for stage in stages:
                # Construct Resolved directly per stage (PR-001) to cover all 20 stages
                resolved = LS.Resolved(
                    stage=stage,
                    style=LS.STAGES[stage],
                    family=LS.FAMILY_BACKLOG,
                )
                for stream_name, make_pair in streams:
                    total_cells += 1
                    term_obj, pal = make_pair()

                    # Two-consumer agreement between Palette.lifecycle and Term.style_lifecycle_text
                    s_term = term_obj.style_lifecycle_text(stage, resolved)
                    s_pal = pal.lifecycle(resolved, stage)
                    if s_term != s_pal:
                        failures.append(
                            f"[{tier}/{stage}/{stream_name}] two-consumer disagreement: "
                            f"Term={s_term!r} != Palette={s_pal!r}"
                        )

                    seams = {
                        "Term.style_lifecycle_text": s_term,
                        "Term.format_lifecycle_marker": term_obj.format_lifecycle_marker(
                            resolved
                        ),
                        "Term.format_lifecycle_compact": term_obj.format_lifecycle_compact(
                            "abc123", resolved
                        ),
                        "Palette.lifecycle": s_pal,
                        "Palette.lifecycle_glyph": pal.lifecycle_glyph(resolved),
                    }

                    for seam_name, out in seams.items():
                        total_seam_evaluations += 1
                        if tier == T.DEPTH_NONE:
                            if "\033" in out:
                                failures.append(
                                    f"[{tier}/{stage}/{stream_name}/{seam_name}] "
                                    f"unexpected escape in none tier: {out!r}"
                                )
                        elif tier == T.DEPTH_16:
                            if "38;5;" in out:
                                failures.append(
                                    f"[{tier}/{stage}/{stream_name}/{seam_name}] "
                                    f"38;5; escape found in 16 tier: {out!r}"
                                )
                            if "\033[" not in out:
                                failures.append(
                                    f"[{tier}/{stage}/{stream_name}/{seam_name}] "
                                    f"expected SGR escape in 16 tier: {out!r}"
                                )
                        elif tier == T.DEPTH_256:
                            if "38;5;" not in out:
                                failures.append(
                                    f"[{tier}/{stage}/{stream_name}/{seam_name}] "
                                    f"expected 38;5; escape in 256 tier: {out!r}"
                                )

        expected_cells = len(stages) * len(tiers) * len(streams)
        expected_evaluations = expected_cells * 5
        self.assertEqual(total_cells, expected_cells)
        self.assertEqual(total_seam_evaluations, expected_evaluations)

        self.assertEqual(
            failures,
            [],
            f"Seam sweep failed {len(failures)}/{total_seam_evaluations} evaluations:\n"
            + "\n".join(failures[:20]),
        )


class LifecycleColorDepthCrossSurfaceCliTests(unittest.TestCase):
    """End-to-end CLI guard across terminal surfaces on a synthesized fixture repo (E-04).

    Residual exposure and limits (E-05):
    1. Covers the LIFECYCLE axis only: generic color output (paths, badges, status)
       ignores color_depth per F-08 (tracked in backlog item cvtg9u), so assertions
       on the 'none' tier are scoped strictly to lifecycle tokens rather than blanket
       escape absence.
    2. Proves the CLI command(s) driven against the synthesized fixture, exercising
       the full real subprocess execution path, but is a sample rather than an exhaustive
       sweep across every CLI subcommand (which was measured at 108s+ over live corpus).
    3. The ladder is CAUGHT, not structurally PREVENTED: no mechanical rule forbids a
       new renderer from re-deriving a tier, but any surface reaching the CLI output
       exercised here is guarded by these observable byte assertions.
    """

    def setUp(self):
        self._repo_root = str(Path(__file__).resolve().parent.parent)

    def _extract_styled_lifecycle_spans(
        self, stdout: str, native_words: set[str]
    ) -> list[tuple[str, str]]:
        spans: list[tuple[str, str]] = []
        for match in re.finditer(r"\033\[([0-9;]+)m([^\033]+)", stdout):
            codes = match.group(1)
            text = match.group(2).strip()
            parts = [p for p in codes.split(";") if p]
            is_styled = bool(parts and not all(p == "0" for p in parts))
            if text in native_words and is_styled:
                spans.append((codes, text))
        return spans

    def test_cross_surface_cli_color_depth_ladder(self):
        # Derive native lifecycle words at runtime from NATIVE_MAPS
        native_words: set[str] = set()
        for family_map in LS.NATIVE_MAPS.values():
            native_words.update(family_map.keys())

        with tempfile.TemporaryDirectory() as fixture_dir, tempfile.TemporaryDirectory() as config_dir:
            # Synthesize fixture repo with 4 items across 4 states (P16 location independence)
            subprocess.run(["git", "init", "-q"], cwd=fixture_dir, check=True)
            states = ["open", "blocked", "done", "graduated"]
            for idx, st in enumerate(states, 1):
                d = Path(fixture_dir) / ".aw" / "records" / "backlog" / st
                d.mkdir(parents=True, exist_ok=True)
                fname = f"20261001-item0{idx}-01-item0{idx}-sample-{st}.backlog.md"
                content = (
                    f"# Backlog: Sample {st}\n\n"
                    f"- Id: item0{idx}\n"
                    f"- Status: {st}\n"
                    f"- Set: item0{idx}\n"
                    f"- Priority: low\n"
                    f"- Work-Kind: chore\n"
                    f"- Summary: Sample item for testing {st}\n"
                )
                (d / fname).write_text(content, encoding="utf-8")

            child_env = os.environ.copy()
            child_env["XDG_CONFIG_HOME"] = config_dir
            child_env["AW_NO_REEXEC"] = "1"
            child_env["TERM"] = "xterm-256color"
            child_env["PYTHONPATH"] = self._repo_root
            for k in ("NO_COLOR", "FORCE_COLOR", "COLORTERM"):
                child_env.pop(k, None)

            # Confirm subprocess imports repository's own package under test (F-10)
            verify_imp = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    "import agent_workflows; print(agent_workflows.__file__)",
                ],
                env=child_env,
                capture_output=True,
                text=True,
                check=True,
            )
            self.assertTrue(
                verify_imp.stdout.strip().startswith(self._repo_root),
                f"Subprocess imported wrong package: {verify_imp.stdout.strip()} (expected within {self._repo_root})",
            )

            def _pin_tier(tier: str) -> None:
                subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "agent_workflows",
                        "config",
                        "set",
                        "color_depth",
                        tier,
                    ],
                    env=child_env,
                    cwd=fixture_dir,
                    check=True,
                    capture_output=True,
                )

            # Commands to test (each must produce lifecycle words to be non-vacuous per PR-002)
            commands = [
                ("find backlog", ["find", "backlog", "--color"]),
            ]

            for cmd_name, cmd_args in commands:
                # Cell 1 (256 tier): Anti-vacuity cell. At least one lifecycle word sits in a 38;5; span
                _pin_tier("256")
                res_256 = subprocess.run(
                    [sys.executable, "-m", "agent_workflows", *cmd_args],
                    env=child_env,
                    cwd=fixture_dir,
                    capture_output=True,
                    text=True,
                    check=True,
                )
                spans_256 = self._extract_styled_lifecycle_spans(
                    res_256.stdout, native_words
                )
                self.assertGreater(
                    len(spans_256),
                    0,
                    f"[{cmd_name}] Anti-vacuity check failed: no lifecycle words found in 256 output",
                )
                self.assertTrue(
                    any("38;5;" in code for code, _ in spans_256),
                    f"[{cmd_name}] Expected 38;5; escape for lifecycle words in 256 pin output, got: {spans_256}",
                )

                # Cell 2 (16 tier): NO lifecycle word sits in a 38;5; span AND at least one is still styled
                _pin_tier("16")
                res_16 = subprocess.run(
                    [sys.executable, "-m", "agent_workflows", *cmd_args],
                    env=child_env,
                    cwd=fixture_dir,
                    capture_output=True,
                    text=True,
                    check=True,
                )
                spans_16 = self._extract_styled_lifecycle_spans(
                    res_16.stdout, native_words
                )
                self.assertGreater(
                    len(spans_16),
                    0,
                    f"[{cmd_name}] Expected styled lifecycle words in 16 pin output",
                )
                self.assertFalse(
                    any("38;5;" in code for code, _ in spans_16),
                    f"[{cmd_name}] Expected no 38;5; escape for lifecycle words in 16 pin output, got: {spans_16}",
                )

                # Cell 3 (none tier): NO lifecycle word is styled at all (token-scoped per F-08)
                _pin_tier("none")
                res_none = subprocess.run(
                    [sys.executable, "-m", "agent_workflows", *cmd_args],
                    env=child_env,
                    cwd=fixture_dir,
                    capture_output=True,
                    text=True,
                    check=True,
                )
                spans_none = self._extract_styled_lifecycle_spans(
                    res_none.stdout, native_words
                )
                self.assertEqual(
                    spans_none,
                    [],
                    f"[{cmd_name}] Expected no styled lifecycle words at color_depth=none, got: {spans_none}",
                )


if __name__ == "__main__":
    unittest.main()
