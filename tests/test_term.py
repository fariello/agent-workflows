"""Tests for agent_workflows.term accessible styling (IPD-2 Batch D; AC-15)."""

from __future__ import annotations

import contextlib
import inspect
import io
import os
import re
import tempfile
import unittest

from agent_workflows import cli
from agent_workflows import config as CFG
from agent_workflows import lifecycle_style as LS
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
        self.assertEqual(len(T.STAGE_COLOR_16), 20)

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


if __name__ == "__main__":
    unittest.main()
