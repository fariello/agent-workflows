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


# ======================================================================================
# THE AUTHORITATIVE EXPECTATION GRID (IPD `z8ddk0` E-05).
#
# WHY A TABLE AND NOT MORE ONE-OFF CASES. Before this plan, NOT ONE empty-string or `'0'`
# case was pinned anywhere in the suite, which is precisely why four measured defects
# survived indefinitely: the behavior was ACCIDENTAL rather than contractual. Three
# independent implementations of this decision had drifted apart, and `FORCE_COLOR=0`
# FORCED COLOR ON because the string `"0"` is truthy in Python, i.e. the value a user
# writes to mean "off" produced its exact opposite, even into a pipe.
#
# EXPECTATIONS ARE WRITTEN OUT, NEVER COMPUTED from the implementation. A grid that
# derives its own expected values passes for any behavior at all, including the broken
# one, so every cell below is a stated contract a reviewer can dispute. The values are
# the maintainer's 2026-09-19 ruling (backlog `nyz8dt`) made concrete.
#
# THE `NO_COLOR`-SET CELLS ARE THE POINT, not filler. The correct composition and the
# tempting NAIVE edit (correcting only the truthiness read at the forcing site while
# leaving the presence read that cancels `NO_COLOR`) agree wherever `NO_COLOR` is unset and
# DISAGREE on SIX cells: measured at execution 2026-09-19, the naive edit colorizes every
# cell where `NO_COLOR` is set AND `FORCE_COLOR` is present-but-falsey, on a TTY, including
# `NO_COLOR=1 FORCE_COLOR=0` - silently voiding the accessibility convention for any user
# who sets both. (The plan predicted twelve; the six with `FORCE_COLOR` UNSET stay plain,
# because there the naive presence test is still the correct test. Six cells, recorded as
# six.) A grid pinning only the headline `FORCE_COLOR='0'` case would pass for that edit.
# These six are what make it fail, and the failure names each cell.
# ======================================================================================

#: The four values each variable is pinned at: absent, present-but-empty, falsey, truthy.
_ENV_VALUES = (None, "", "0", "1")


def _env_label(value: str | None) -> str:
    return "unset" if value is None else (value if value else "empty")


#: `(NO_COLOR, FORCE_COLOR) -> (expected_on_a_tty, expected_on_a_pipe)`, at a capable TERM.
#:
#: READING THE ROWS. `NO_COLOR` is PRESENCE-ONLY, so any setting of it suppresses (row 2
#: onward is plain) UNLESS `FORCE_COLOR` genuinely forces. `FORCE_COLOR` INTERPRETS its
#: value, so only `'1'` forces; `''` and `'0'` mean "do not force" and fall through to
#: ordinary TTY detection rather than suppressing (suppressing is `NO_COLOR`'s job).
_COLOR_GRID: dict[tuple[str | None, str | None], tuple[bool, bool]] = {
    # NO_COLOR unset: ordinary detection, except a forcing FORCE_COLOR beats the pipe.
    (None, None): (True, False),
    (None, ""): (True, False),
    # THE HEADLINE DEFECT (F-01): this cell was (True, True) before the fix, i.e. a
    # falsey FORCE_COLOR forced color all the way into a pipe.
    (None, "0"): (True, False),
    (None, "1"): (True, True),
    # NO_COLOR present-but-EMPTY still suppresses: the convention is presence, not value.
    ("", None): (False, False),
    ("", ""): (False, False),
    ("", "0"): (False, False),
    ("", "1"): (True, True),
    # NO_COLOR='0' suppresses TOO. It looks falsey, and that is deliberate: no-color.org
    # says "when present, regardless of its value", and reinterpreting an external
    # accessibility convention repo-locally would be worse than the asymmetry with
    # FORCE_COLOR (which is ours to interpret and which users do write `0` into).
    ("0", None): (False, False),
    ("0", ""): (False, False),
    ("0", "0"): (False, False),
    ("0", "1"): (True, True),
    ("1", None): (False, False),
    ("1", ""): (False, False),
    # THE F-05 CELL. A user who sets NO_COLOR AND a falsey FORCE_COLOR must still get
    # PLAIN: the falsey value means "do not force", never "cancel NO_COLOR". The naive
    # single-site edit returns color here, which is strictly worse than the bug being
    # fixed, so this one cell is the difference between the two implementations.
    ("1", "0"): (False, False),
    # PRESERVED DELIBERATELY: a genuinely forcing FORCE_COLOR still beats NO_COLOR, which
    # is today's behavior and which the maintainer's ruling keeps
    # (`test_force_color_overrides_no_color` above pins the same cell).
    ("1", "1"): (True, True),
}

#: `TERM -> (expected_on_a_tty, expected_on_a_pipe)`, with both variables unset.
_TERM_GRID: dict[str | None, tuple[bool, bool]] = {
    "xterm-256color": (True, False),
    # `dumb` is the cell `runner_shared` disagreed on: it ignored TERM entirely, so
    # `TERM=dumb aw oc run` emitted color while `TERM=dumb aw attention` did not.
    "dumb": (False, False),
    "": (False, False),
    None: (False, False),
}


class ShouldColorGridTests(unittest.TestCase):
    """Every cell of the two measured grids, each as a separately named expectation."""

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

    def test_the_grid_covers_every_combination_exhaustively(self):
        """Guard the guard: a table with a missing row is a silently unpinned cell."""
        self.assertEqual(
            sorted(_COLOR_GRID, key=lambda k: (str(k[0]), str(k[1]))),
            sorted(
                ((nc, fc) for nc in _ENV_VALUES for fc in _ENV_VALUES),
                key=lambda k: (str(k[0]), str(k[1])),
            ),
            "the NO_COLOR x FORCE_COLOR grid must pin all 16 combinations",
        )
        self.assertEqual(len(_COLOR_GRID) * 2, 32, "16 cells x 2 stream kinds")
        self.assertEqual(
            sorted(_TERM_GRID, key=str),
            sorted(("xterm-256color", "dumb", "", None), key=str),
            "the TERM axis must pin a capable value, `dumb`, empty, and absent",
        )

    def test_every_no_color_force_color_cell_matches_the_ruled_expectation(self):
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

    def test_every_term_value_matches_the_ruled_expectation(self):
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

    def test_a_falsey_force_color_never_forces_and_never_suppresses(self):
        """The ruling's own words, asserted directly rather than only via the grid.

        Stated separately because it is the SEMANTIC claim: a falsey `FORCE_COLOR` is not
        an instruction to suppress, it is the ABSENCE of an instruction to force, so it
        must behave exactly as an unset variable does.
        """
        for value in ("", "0", "false", "FALSE", "no", "off", " 0 "):
            with self.subTest(force_color=value):
                self._apply(NO_COLOR=None, FORCE_COLOR=value, TERM="xterm-256color")
                self.assertTrue(
                    T.should_color(_FakeTTY()),
                    f"FORCE_COLOR={value!r} must fall through to detection, not suppress",
                )
                self.assertFalse(
                    T.should_color(_FakePipe()),
                    f"FORCE_COLOR={value!r} must not force color into a pipe",
                )


class OneOriginatingDefinitionTests(unittest.TestCase):
    """Exactly ONE originating `should_color` in the package (IPD `z8ddk0` E-07).

    THE MECHANICAL PROPERTY spec `uonrjg` R9.3a.2 demands: the depth resolver above this
    decision cannot honestly claim one definition while the decision beneath it has three,
    which is what it had - measured by execution 2026-09-19, `term.py`, `runner_shared.py`
    and `pwatch.py` each carried an independent implementation and all three DISAGREED.

    WHY "ORIGINATING" AND NOT "ONE `def`", because the obvious form of this guard is FALSE
    (F-08). `runner_shared` legitimately keeps a one-line DELEGATING `def` at this name -
    three shipped guards assert that module defines the symbol, so an import fails them -
    and a delegation is syntactically a `def`. So `grep -c "def should_color"` returns TWO
    on a correct tree, and a guard asserting ONE would be permanently red. The rule is
    therefore: exactly one top-level `def should_color` is not a pure delegation, and it is
    in `term.py`. That is the same distinction `is_pure_delegation`
    (`tests/test_rununify_run_queue.py:250`) already draws for the runner seam; the
    predicate is reimplemented here rather than imported ONLY because that one hard-codes
    `runner_shared` as the delegation TARGET, and this seam delegates to `term`.

    AST, NOT SUBSTRING. The file-local convention is recorded in
    `tests/test_runner_refork_guard.py`'s docstring: an `assertNotIn("class Palette:", src)`
    guard was once evaded by whitespace and separately satisfied by a mere comment.
    """

    SYMBOL = "should_color"

    @staticmethod
    def _package_dir():
        import pathlib

        return pathlib.Path(str(T.__file__)).parent

    @classmethod
    def _definition_sites(cls) -> dict[str, list[tuple[str, int, bool]]]:
        """Map module name -> [(module, lineno, is_delegation)] for every top-level def."""
        import ast

        sites: dict[str, list[tuple[str, int, bool]]] = {}
        for path in sorted(cls._package_dir().glob("*.py")):
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"))
            except SyntaxError:  # pragma: no cover - a broken module is another failure
                continue
            for node in tree.body:
                if (
                    isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and node.name == cls.SYMBOL
                ):
                    sites.setdefault(path.name, []).append(
                        (path.name, node.lineno, cls._is_pure_delegation(node))
                    )
        return sites

    @staticmethod
    def _is_pure_delegation(node) -> bool:
        """One statement returning a single call whose callee is an ATTRIBUTE of a module.

        Deliberately does NOT pin the target module name: what makes a wrapper safe is that
        it holds no logic of its own, not which module it forwards to.

        A DOCSTRING AND AN `import` ARE SUBTRACTED, both because neither is logic. The import
        is not a stylistic allowance: `runner_shared` is FORBIDDEN from importing `term` at
        module level by
        `tests/test_orchestrator_probe_cache.py::test_no_new_module_level_first_party_import_in_runner_shared`
        (measured 2026-09-19 - it allows only `render_stream` and `runner_profiles`, since an
        import there changes the graph for both host drivers), and that guard's docstring
        names the function-local import as this module's established route. So the sanctioned
        delegation shape AT THIS SEAM is necessarily `import` + `return`, and a predicate
        demanding literally one statement would forbid the only legal spelling. What still
        makes the check bite is that ONLY imports are subtracted: any conditional,
        assignment, or environment read keeps the body impure, which
        `test_the_delegation_predicate_refuses_a_body_with_logic` proves.
        """
        import ast

        body = [
            stmt
            for stmt in node.body
            if not (
                isinstance(stmt, ast.Expr)
                and isinstance(stmt.value, ast.Constant)
                and isinstance(stmt.value.value, str)
            )
            and not isinstance(stmt, (ast.Import, ast.ImportFrom))
        ]
        if len(body) != 1:
            return False
        stmt = body[0]
        value = stmt.value if isinstance(stmt, (ast.Return, ast.Expr)) else None
        if not isinstance(value, ast.Call):
            return False
        return isinstance(value.func, ast.Attribute) and isinstance(
            value.func.value, ast.Name
        )

    def test_exactly_one_originating_definition_and_it_is_in_term(self):
        originating = [
            (module, lineno)
            for entries in self._definition_sites().values()
            for (module, lineno, is_delegation) in entries
            if not is_delegation
        ]
        self.assertEqual(
            [module for module, _ in originating],
            ["term.py"],
            "the color capability decision must have EXACTLY ONE originating definition, "
            f"in `term.py`; found {originating}. A new module must CALL "
            "`term.should_color` (or delegate to it in one statement), never reimplement "
            "it: three independent implementations had already drifted into three "
            "different behaviors (IPD `z8ddk0`)",
        )

    def test_the_known_delegation_is_recognized_rather_than_counted_as_a_fork(self):
        """The INVERSE. Without it the guard could pass by rejecting legal delegations,
        which would force a future author to break `runner_shared`'s three guards."""
        sites = self._definition_sites()
        self.assertIn(
            "runner_shared.py",
            sites,
            "`runner_shared` must keep its delegating `def should_color`; three shipped "
            "guards assert that module DEFINES the symbol",
        )
        self.assertTrue(
            all(is_delegation for (_m, _l, is_delegation) in sites["runner_shared.py"]),
            "`runner_shared.should_color` is no longer a pure delegation, so the symbol "
            "has been RE-FORKED",
        )


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
        """`status_256` styles a GENERIC role word, padded to width.

        RE-POINTED FROM `open` TO `updated` (plan `qdd5jq` E-04, spec `uonrjg` R10.3, criterion A17).
        This asserted `open` -> 40, but `open` is a BACKLOG LIFECYCLE status (spec Section 6.3, stage
        `ready`), and the whole point of E-04's split is that a lifecycle status no longer resolves
        through this second table. Lifecycle words now go through `style_lifecycle_text`, which the
        `LifecycleRendering` tests below cover; `status_256` retains only the generic command-outcome
        and formatting roles R10.3 keeps valid. So the method's REAL contract (a role color, bold, and
        padding to a visible width) is asserted with a word that is genuinely one of those roles.
        """

        t_color = T.Term(stream=io.StringIO(), color=True)
        out = t_color.status_256("updated", width=12)
        self.assertIn("\033[1;38;5;46mupdated\033[0m", out)
        self.assertEqual(len(_ANSI.sub("", out)), 12)

        t_plain = T.Term(stream=io.StringIO(), color=False)
        out_plain = t_plain.status_256("updated", width=12)
        self.assertEqual(out_plain, "updated     ")

        # THE NEGATIVE HALF, which is what makes the split falsifiable rather than merely described:
        # a LIFECYCLE status must NOT resolve a lifecycle color here any more. It falls back to the
        # neutral 244 every unmapped word gets, because this table no longer knows lifecycle at all.
        for lifecycle_status in (
            "open",
            "approved",
            "executed",
            "draft",
            "implementing",
        ):
            with self.subTest(status=lifecycle_status):
                self.assertNotIn(lifecycle_status, T.ROLE_COLOR_256)
                self.assertIn(
                    "\033[1;38;5;244m",
                    t_color.status_256(lifecycle_status),
                    f"{lifecycle_status!r} still resolves a color from the generic role table; "
                    "spec criterion A17 requires lifecycle color to come only from lifecycle_style",
                )

    def test_attention_holds_no_lifecycle_palette_of_its_own(self):
        """`attention.py` owns NO lifecycle color table; it consumes the shared resolver.

        RE-POINTED, NOT DELETED (plan `f9t5hz` E-01 / V-01). This test used to iterate
        `attention._STATUS_COLOR_256` and assert every entry matched `term.STATUS_COLOR_256`, i.e. it
        was a DRIFT GUARD between two live lifecycle tables. `f9t5hz` removed the second table, so
        the old assertion could not survive in any form: the symbol it imported is gone and the test
        would have failed as an `AttributeError` rather than as a palette mismatch.

        THE PURPOSE IS PRESERVED AND STRENGTHENED rather than dropped, which is why this is a
        re-point. The old test could only catch two tables DISAGREEING; this one catches a second
        table EXISTING at all, which is the condition spec `uonrjg` R10.3 and criterion A17 actually
        require ("Local `_STATUS_COLOR_256` lifecycle tables MUST be removed"). Deleting the test
        outright would have left nothing asserting that the module stayed converted.
        """

        from agent_workflows import attention as att
        from agent_workflows import attention_contract as A

        self.assertFalse(
            hasattr(att, "_STATUS_COLOR_256"),
            "attention.py must hold no local lifecycle status palette (spec uonrjg R10.3); "
            "lifecycle color comes from lifecycle_style via term.",
        )
        # `_CLASS_COLOR_256` SURVIVES ON PURPOSE and is NOT a lifecycle table: its keys are the
        # five cross-tree ATTENTION CLASS constants, which spec Section 3 lists as an explicit
        # NON-GOAL, and it colors only the board's section headers.
        self.assertTrue(hasattr(att, "_CLASS_COLOR_256"))
        self.assertEqual(
            set(att._CLASS_COLOR_256),
            {A.ACTIVE, A.READY, A.BLOCKED, A.DONE, A.PARKED},
        )

    def test_attention_lifecycle_color_comes_from_the_shared_table(self):
        """A rendered attention status word carries `lifecycle_style`'s color, not a local one.

        The companion to the test above: that one proves no second TABLE exists, this one proves the
        rendered bytes actually come from the FIRST one. Together they are what the retired
        cross-module drift guard was reaching for.
        """

        from agent_workflows import attention as att
        from agent_workflows import attention_contract as A

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
        self.assertIn(
            f"\033[1;38;5;{expected.style.color}mopen\033[0m",
            out,
            "the status word must be painted with lifecycle_style's index for its stage",
        )


class CliNeverLeaksTheColorOverrideTests(unittest.TestCase):
    """No `cli.main` exit path may leave the process-wide color override set.

    THE FLAKE THIS CLOSES, measured 2026-09-20. `cli._dispatch` sets the override from the parsed
    flags part way through its body. `argparse`'s `--help` and its usage errors raise `SystemExit`
    from inside that body, so `cli.main(["--no-color", "check", "--help"])` used to leave the
    override at `False` for the rest of the process, after which `term.should_color(<a tty>)`
    answered `False` for every later caller. Fifteen test files pass `--color`/`--no-color` to a CLI
    entry point, so under `pytest-xdist` whichever color-detection test `pytest-randomly` happened
    to schedule after one of them in the same worker FAILED, while that same test passed when its
    file ran alone. Four runs in six passed by luck, which is why it read as an unrelated flake and
    once cost a merge gate about two hours.

    WHY THIS SHAPE. Each row drives a REAL `cli.main` on a path that leaves `_dispatch` early, then
    asserts the override is back to what it was AND that `should_color` on a terminal still answers
    True. Asserting the override alone would miss a restore that writes some other wrong value;
    asserting `should_color` alone would not say which layer broke. The rows are exit PATHS, not
    flags, because the flag was never the interesting variable: the leak needed an early exit.
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
        T.set_color_override(None)

    def _restore(self):
        for k, v in self._saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    #: (case, argv, why this row exists)
    EARLY_EXIT_PATHS = (
        (
            "--no-color then a subcommand --help (argparse raises SystemExit)",
            ["--no-color", "check", "--help"],
            "THE MEASURED CASE. `--help` never reaches the end of `_dispatch`, so before the fix "
            "the override stayed False for the whole process",
        ),
        (
            "--color then a subcommand --help",
            ["--color", "check", "--help"],
            "the opposite polarity: a leaked True is just as wrong, and forces color into a pipe "
            "for every later caller",
        ),
        (
            "--no-color then top-level --help",
            ["--no-color", "--help"],
            "the top-level help path exits even earlier than the subcommand one",
        ),
        (
            "--no-color then an unknown verb (argparse usage error)",
            ["--no-color", "definitely-not-a-verb"],
            "a usage error is the other SystemExit route out of the same body, and an operator "
            "typo must not restyle the rest of the process",
        ),
        (
            "--color with no verb at all",
            ["--color"],
            "the no-subcommand path prints help and returns; it must reset like every other",
        ),
    )

    def test_no_early_exit_path_leaves_the_override_set(self):
        class _TTY(io.StringIO):
            def isatty(self):
                return True

        wrong = []
        for case, argv, why in self.EARLY_EXIT_PATHS:
            T.set_color_override(None)
            buf = io.StringIO()
            try:
                with (
                    contextlib.redirect_stdout(buf),
                    contextlib.redirect_stderr(buf),
                ):
                    cli.main(list(argv))
            except SystemExit:
                pass  # argparse's own exit is one of the paths under test
            problems = []
            left = T.get_color_override()
            if left is not None:
                problems.append(
                    f"the override was left at {left!r}; every later caller in this process "
                    "now inherits a presentation choice made by an unrelated invocation"
                )
            if not T.should_color(_TTY()):
                problems.append(
                    "should_color() on a REAL TTY answered False, which is the observable "
                    "symptom: any later color-detection test in this worker now fails"
                )
            if problems:
                wrong.append(
                    f"  {case}\n    argv: {argv!r}\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} of {len(self.EARLY_EXIT_PATHS)} `cli.main` exit paths leaked the "
            "process-wide color override. THIS IS A SUITE-WIDE FLAKE, not a local failure: the "
            "leak poisons every later `should_color` call in the same process, so under xdist an "
            "unrelated color test in the same worker fails and the failing test moves run to run "
            "with the random order. FIX: `cli.main` restores the override it INHERITED in a "
            "`finally`, so the return path, the `SystemExit` path and the exception path are all "
            f"covered. Do not move the reset in `_dispatch`; a verb may read it.\n"
            + "\n".join(wrong),
        )

    def test_a_nested_invocation_preserves_an_outer_override(self):
        """The restore must put back what it INHERITED, not blindly `None`.

        Kept separate because it asserts the opposite direction from the table: the runners set an
        override around a block of work and then launch nested `aw` invocations, so a reset to
        `None` would silently discard a caller's deliberate choice. A fix that always cleared would
        pass the table above and break this.
        """
        T.set_color_override(True)
        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
                cli.main(["check", "--help"])
        except SystemExit:
            pass
        self.assertIs(
            T.get_color_override(),
            True,
            "a nested `aw` invocation cleared an override its caller had deliberately set; the "
            "restore must return the INHERITED value, not None",
        )


# ======================================================================================
# THE COLOR-DEPTH LADDER (spec `uonrjg` R9.3a.1-R9.3a.5; criteria A12a-A12d; plan `pow5sj`)
# ======================================================================================


class _DepthTestBase(unittest.TestCase):
    """Shared env/config isolation for the depth tests.

    REUSES THE SHIPPED HARNESS above (`_FakeTTY`, `_FakePipe`, and the save/restore `setUp`
    pattern) rather than introducing a second stream-double convention, which the plan's
    Required-tests section requires explicitly.

    THE CONFIG STORE IS REDIRECTED TO A TEMPORARY DIRECTORY for every test in this group, because
    the depth resolver's pin rung READS THE USER'S CONFIG FILE. Without this, a maintainer who had
    actually pinned a depth would see these tests fail on their machine and pass in CI, and worse,
    a test that WROTE a pin would edit the developer's real config.
    """

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
        """A 256-capable TTY environment: the baseline every rung is measured against."""
        for k in ("NO_COLOR", "FORCE_COLOR", "COLORTERM"):
            os.environ.pop(k, None)
        os.environ["TERM"] = "xterm-256color"

    def _pin(self, value):
        CFG.set_config_value("color_depth", value)


class ColorDepthPrecedenceTests(_DepthTestBase):
    """A12a: every rung of the R9.3a.2 chain, each asserted SEPARATELY.

    ONE TEST PER RUNG, never one composite case, because A12a requires it in as many words
    ("Assert each rung explicitly") and because a composite assertion cannot say WHICH rung broke.
    """

    # --- Rung 1: color is off entirely -> `none` --------------------------------------
    def test_rung1_no_color_yields_none(self):
        self._capable_tty()
        os.environ["NO_COLOR"] = "1"
        self.assertEqual(T.resolve_color_depth(_FakeTTY()), T.DEPTH_NONE)

    def test_rung1_term_dumb_yields_none(self):
        self._capable_tty()
        os.environ["TERM"] = "dumb"
        self.assertEqual(T.resolve_color_depth(_FakeTTY()), T.DEPTH_NONE)

    def test_rung1_non_tty_yields_none(self):
        self._capable_tty()
        self.assertEqual(T.resolve_color_depth(_FakePipe()), T.DEPTH_NONE)

    def test_rung1_no_color_flag_override_yields_none(self):
        """`--no-color` reaches the resolver as `override=False`, never through os.environ.

        Asserted because the flag is the ONE top-rung input the resolver cannot see in the
        environment: `term` never reads argparse (a nested `aw` process would inherit an env var and
        be silently restyled), so a resolver that only consulted the environment would drop
        `--no-color` from R9.3a.2's top rung entirely.
        """
        self._capable_tty()
        self.assertEqual(
            T.resolve_color_depth(_FakeTTY(), override=False), T.DEPTH_NONE
        )

    def test_rung1_process_wide_no_color_override_yields_none(self):
        self._capable_tty()
        T.set_color_override(False)
        self.assertEqual(T.resolve_color_depth(_FakeTTY()), T.DEPTH_NONE)

    # --- THE CASE THE SPEC SINGLES OUT ------------------------------------------------
    def test_no_color_beats_a_pinned_depth(self):
        """A12a's named case: `NO_COLOR` with a pinned depth STILL yields plain text.

        ITS OWN TEST, not a cell in a grid, because R9.3a.2 calls this "the one an implementation is
        most likely to get backwards" and the reason is a real design tension: a pin is the user
        asking for color, and honoring the more specific instruction is normally right. Here it is
        wrong, because `NO_COLOR` is an ACCESSIBILITY CONVENTION and a preference may not defeat a
        convention. A user who wants color pins a depth AND does not set `NO_COLOR`.
        """
        self._capable_tty()
        self._pin("256")
        self.assertEqual(
            T.resolve_color_depth(_FakeTTY()),
            T.DEPTH_256,
            "sanity: the pin must be in force before NO_COLOR is introduced",
        )
        os.environ["NO_COLOR"] = "1"
        self.assertEqual(
            T.resolve_color_depth(_FakeTTY()),
            T.DEPTH_NONE,
            "a pinned depth DEFEATED NO_COLOR; R9.3a.2 forbids a preference overriding an "
            "accessibility convention",
        )

    def test_no_color_beats_a_pinned_16_as_well(self):
        """The same rule at the middle tier, so the guard is not accidentally 256-specific."""
        self._capable_tty()
        self._pin("16")
        os.environ["NO_COLOR"] = "1"
        self.assertEqual(T.resolve_color_depth(_FakeTTY()), T.DEPTH_NONE)

    def test_force_color_still_overrides_no_color_at_the_depth_resolver(self):
        """OQ-02, ruled READING A by the maintainer 2026-09-19: the escape hatch SURVIVES.

        The spec specifies this rung twice and incompatibly (R9.3a.2 calls `NO_COLOR` "unconditional"
        while Section 9.3 requires preserving current `FORCE_COLOR` behavior, under which
        `FORCE_COLOR` wins). The ruling: `FORCE_COLOR` keeps its override, and "unconditional" is
        unconditional with respect to the DEPTH PIN only. This test pins the ruled behavior at the
        DEPTH seam, exactly as `test_force_color_overrides_no_color` pins it at the boolean seam.
        """
        self._capable_tty()
        os.environ["NO_COLOR"] = "1"
        os.environ["FORCE_COLOR"] = "1"
        self.assertEqual(T.resolve_color_depth(_FakePipe()), T.DEPTH_256)

    # --- Rung 2: an explicit pin beats detection --------------------------------------
    def test_rung2_a_pinned_depth_overrides_detection(self):
        self._capable_tty()  # detection would say 256
        self._pin("16")
        self.assertEqual(
            T.resolve_color_depth(_FakeTTY()),
            T.DEPTH_16,
            "a pinned 16 was overruled by 256-color detection; the pin outranks detection",
        )

    def test_rung2_a_pinned_none_overrides_a_capable_terminal(self):
        self._capable_tty()
        self._pin("none")
        self.assertEqual(T.resolve_color_depth(_FakeTTY()), T.DEPTH_NONE)

    def test_rung2_a_pinned_256_overrides_16_color_detection(self):
        """The pin must win in BOTH directions, not only downward.

        A plausible wrong implementation takes the MINIMUM of the pin and detection, which passes
        the two tests above (both pin downward) and fails here. A pin is the user's statement about
        their own terminal, so it replaces detection rather than capping it.
        """
        self._capable_tty()
        os.environ["TERM"] = "xterm-16color"
        self._pin("256")
        self.assertEqual(T.resolve_color_depth(_FakeTTY()), T.DEPTH_256)

    # --- Rung 3: detection beats the default ------------------------------------------
    def test_rung3_detection_of_a_16_color_term_overrides_the_default(self):
        self._capable_tty()
        os.environ["TERM"] = "xterm-16color"
        self.assertEqual(
            T.resolve_color_depth(_FakeTTY()),
            T.DEPTH_16,
            "a 16-color TERM fell through to the 256 default; detection outranks the default",
        )

    def test_rung3_detection_of_a_256_color_term_resolves_256(self):
        self._capable_tty()
        self.assertEqual(T.resolve_color_depth(_FakeTTY()), T.DEPTH_256)

    def test_rung3_colorterm_truecolor_resolves_256_not_a_fourth_rung(self):
        """D42's ladder has THREE rungs, so a truecolor terminal tops out at 256."""
        self._capable_tty()
        os.environ["TERM"] = "sometermnobodyknows"
        os.environ["COLORTERM"] = "truecolor"
        self.assertEqual(T.resolve_color_depth(_FakeTTY()), T.DEPTH_256)

    def test_rung3_a_linux_console_resolves_16(self):
        self._capable_tty()
        os.environ["TERM"] = "linux"
        self.assertEqual(T.resolve_color_depth(_FakeTTY()), T.DEPTH_16)

    # --- Rung 4: the default ----------------------------------------------------------
    def test_rung4_the_default_is_256_not_the_conservative_rung(self):
        """R9.3a.2: "the default is 256 rather than the most conservative rung".

        Asserted with an UNRECOGNIZED `TERM`, which is the only state where the default is actually
        reachable. An implementation that degraded an unknown terminal to 16 "to be safe" would be
        the conservative default D42 exists to reject, and it would pass every other test here.
        """
        self._capable_tty()
        os.environ["TERM"] = "sometermnobodyknows"
        self.assertEqual(T.resolve_color_depth(_FakeTTY()), T.DEPTH_256)
        self.assertEqual(T.DEFAULT_COLOR_DEPTH, T.DEPTH_256)

    def test_an_invalid_pin_in_the_file_falls_through_instead_of_raising(self):
        """A hand-edited bad value must not make every styled command crash.

        The REFUSAL belongs at the setter (see the config tests), where the user can fix the typo.
        Here, fail-open to detection is the only safe behavior: a presentation preference must never
        be the reason a command cannot render.
        """
        self._capable_tty()
        cfg = CFG.load()
        cfg["color_depth"] = "tru3color"
        CFG.save(cfg)
        self.assertEqual(T.resolve_color_depth(_FakeTTY()), T.DEPTH_256)


class ColorDepthOneDefinitionTests(unittest.TestCase):
    """A12a: the depth resolver has EXACTLY ONE definition (R9.3a.2).

    Modeled on `OneOriginatingDefinitionTests` above and AST-based for the same recorded reason: a
    substring guard in this repository has twice been evaded by whitespace or satisfied by a mere
    comment.
    """

    SYMBOL = "resolve_color_depth"

    @staticmethod
    def _package_dir():
        import pathlib

        return pathlib.Path(str(T.__file__)).parent

    def test_no_second_depth_detection_path_exists_in_the_package(self):
        """`COLORTERM`/`256color` may be read by the ONE resolver's module and nowhere else.

        This is the guard that keeps the single definition MEANINGFUL. A second module quietly
        grepping `COLORTERM` would be a rival depth decision even while `resolve_color_depth`
        remained unique, which is exactly the fragmentation plan `z8ddk0` had to undo for the
        boolean decision.
        """
        offenders = []
        for path in sorted(self._package_dir().glob("*.py")):
            if path.name == "term.py":
                continue
            text = path.read_text(encoding="utf-8")
            for marker in ("COLORTERM", "256color"):
                if marker in text:
                    offenders.append(f"{path.name} reads {marker}")
        self.assertEqual(
            offenders,
            [],
            "depth detection leaked out of term.py: " + ", ".join(offenders),
        )

    def test_term_gained_no_argparse_awareness(self):
        """F-06: the flag arrives as `override=`, so `term` must not reach for a namespace."""
        text = (self._package_dir() / "term.py").read_text(encoding="utf-8")
        self.assertNotIn("import argparse", text)
        self.assertNotIn("args.no_color", text)


class AuthoredSixteenColorPaletteTests(unittest.TestCase):
    """A12b: the 16-color tier is AUTHORED, and its separations and collapses are pinned."""

    def test_the_palette_covers_every_semantic_stage(self):
        self.assertEqual(
            set(T.STAGE_COLOR_16),
            set(LS.ALL_STAGES),
            "the 16-color palette must cover exactly the semantic stage vocabulary",
        )
        self.assertEqual(len(T.STAGE_COLOR_16), 20)

    def test_the_palette_uses_only_the_sixteen_named_colors(self):
        """A 256-index leaking into this table would defeat the tier's entire purpose."""
        named = set(range(30, 38)) | set(range(90, 98))
        wrong = {
            stage: code for stage, code in T.STAGE_COLOR_16.items() if code not in named
        }
        self.assertEqual(
            wrong, {}, f"non-16-color SGR codes in the 16-color palette: {wrong}"
        )

    def test_ready_is_distinguishable_from_done(self):
        """Separation 1 of 3. Adjacent at 256 (45 versus 46) and opposite in meaning."""
        self.assertNotEqual(T.color_16_for_stage("ready"), T.color_16_for_stage("done"))

    def test_blocked_is_distinguishable_from_failed(self):
        """Separation 2 of 3. Both warm at 256 (208 versus 196)."""
        self.assertNotEqual(
            T.color_16_for_stage("blocked"), T.color_16_for_stage("failed")
        )

    def test_waiting_input_is_distinguishable_from_blocked(self):
        """Separation 3 of 3. The adjacent orange pair R9.3a.4 names as the concrete hazard."""
        self.assertNotEqual(
            T.color_16_for_stage("waiting-input"), T.color_16_for_stage("blocked")
        )

    def test_the_active_subtypes_collapse_to_one_yellow(self):
        """Expected collapse 1: five subtypes plus generic `active`, already one color at 256."""
        group = (
            "reviewing",
            "executing",
            "verifying",
            "integrating",
            "recovering",
            "active",
        )
        codes = {T.color_16_for_stage(stage) for stage in group}
        self.assertEqual(
            len(codes), 1, f"the six active stages must share ONE color; got {codes}"
        )

    def test_the_six_gray_family_stages_collapse_to_one_neutral(self):
        """Expected collapse 2, and note the count is SIX.

        R9.3a.3's prose says "the four grays" and then lists six names. The list is right and the
        word is wrong, which the 256 table settles: five of these sit at 244 and `formative` at 245.
        An implementation that built the neutral for four would leave two stages uncollapsed.
        """
        group = ("parked", "superseded", "abandoned", "unknown", "none", "formative")
        self.assertEqual(len(group), 6)
        codes = {T.color_16_for_stage(stage) for stage in group}
        self.assertEqual(
            len(codes),
            1,
            f"the six gray-family stages must share ONE neutral; got {codes}",
        )

    def test_the_palette_is_not_a_mechanical_reduction_of_the_256_tier(self):
        """R9.3a.3 forbids DERIVING the tier, so prove it is not derived.

        The property that distinguishes authored from derived: at 256 `ready`(45) and `done`(46) are
        adjacent, as are `blocked`(208) and `waiting-input`(214) relative to `failed`(196). Any
        nearest-neighbour reduction merges at least one such pair. This table merges none of them,
        which a derivation cannot achieve.
        """
        for left, right in T.REQUIRED_16_COLOR_SEPARATIONS:
            self.assertNotEqual(
                T.color_16_for_stage(left),
                T.color_16_for_stage(right),
                f"{left} and {right} merged at 16-color",
            )

    def test_the_palette_merges_no_pair_outside_a_named_collapse(self):
        """R9.3a.3 names the collapses it accepts, so an UNNAMED merge is an unreviewed loss.

        THIS TEST FOUND A REAL DEFECT rather than merely documenting a rule (recorded because a guard
        that never fired is weak evidence): the palette's first draft gave `authority-queued` plain
        magenta, the same code as `blocked`. Those are 135 (a purple) and 208 (an orange) at 256, so
        nothing about the 256 tier suggests merging them, and none of the three required separations
        mentions either stage - meaning every other assertion in this class passed. `authority-queued`
        is now bright magenta.
        """
        collapse_members = {
            stage for group in T.EXPECTED_16_COLOR_COLLAPSES for stage in group
        }
        by_code = {}
        for stage, code in T.STAGE_COLOR_16.items():
            by_code.setdefault(code, []).append(stage)
        offenders = {
            code: sorted(s for s in stages if s not in collapse_members)
            for code, stages in by_code.items()
            if len([s for s in stages if s not in collapse_members]) > 1
        }
        self.assertEqual(
            offenders,
            {},
            f"stages merged onto one color with no collapse declared for them: {offenders}",
        )

    def test_the_validator_rejects_an_unnamed_merge(self):
        from unittest import mock

        broken = dict(T.STAGE_COLOR_16)
        broken["authority-queued"] = broken["blocked"]
        with mock.patch.object(T, "STAGE_COLOR_16", broken):
            with self.assertRaises(ValueError) as ctx:
                T.validate_16_color_palette()
        self.assertIn("authority-queued", str(ctx.exception))

    def test_the_validator_rejects_a_merged_separation(self):
        """Guard the guard: the import-time validator must actually catch a regression."""
        from unittest import mock

        broken = dict(T.STAGE_COLOR_16)
        broken["blocked"] = broken["failed"]
        with mock.patch.object(T, "STAGE_COLOR_16", broken):
            with self.assertRaises(ValueError) as ctx:
                T.validate_16_color_palette()
        self.assertIn("blocked", str(ctx.exception))

    def test_the_validator_rejects_a_missing_stage(self):
        from unittest import mock

        broken = dict(T.STAGE_COLOR_16)
        broken.pop("ready")
        with mock.patch.object(T, "STAGE_COLOR_16", broken):
            with self.assertRaises(ValueError) as ctx:
                T.validate_16_color_palette()
        self.assertIn("ready", str(ctx.exception))

    def test_the_validator_rejects_a_split_collapse(self):
        """The collapses are pinned so a later change cannot quietly re-expand them."""
        from unittest import mock

        broken = dict(T.STAGE_COLOR_16)
        broken["verifying"] = (
            34  # blue: a color a 16-color terminal shows, but a split group
        )
        with mock.patch.object(T, "STAGE_COLOR_16", broken):
            with self.assertRaises(ValueError) as ctx:
                T.validate_16_color_palette()
        self.assertIn("collapse", str(ctx.exception))


class EveryTierKeepsTheInvariantTests(_DepthTestBase):
    """A12d / R9.3a.5: at 256, at 16, and at none, the glyph AND the native word are present.

    ONE FIXTURE RENDERED AT ALL THREE TIERS, as A12d requires, so the invariant is asserted against
    the same input rather than against three hand-written expectations that could each be wrong in a
    compensating way.
    """

    #: One row per fixture entry: (family, native status). Chosen to include both members of all
    #: three required separations plus one member of each expected collapse, so the fixture actually
    #: exercises the distinctions the tier is required to preserve.
    FIXTURE = (
        ("plans", "approved"),  # -> ready
        ("plans", "executed"),  # -> done
        ("backlog", "blocked"),  # -> blocked
        ("runner-item", "failed"),  # -> failed
        ("runner-item", "needs_input"),  # -> waiting-input
        ("specs", "implementing"),  # -> executing (active collapse)
        ("specs", "parked"),  # -> parked (gray collapse)
    )

    def _render(self, tier):
        """Render the fixture at ``tier``, returning ``[(stage, native_word, line)]``.

        The renderer here is deliberately MINIMAL and local: the shared rendering helpers are
        sibling `bn026f`'s work, so this test must not presume them. What it asserts is the
        INVARIANT (glyph plus word at every tier), which does not depend on which helper draws them.
        """
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

    def test_the_glyph_and_the_word_are_present_at_every_tier(self):
        for tier in (T.DEPTH_256, T.DEPTH_16, T.DEPTH_NONE):
            for stage, native, line in self._render(tier):
                plain = T.strip_ansi(line)
                with self.subTest(tier=tier, stage=stage):
                    self.assertIn(
                        native,
                        plain,
                        f"the native word vanished at tier {tier}",
                    )
                    self.assertIn(
                        LS.STAGES[stage].unicode,
                        plain,
                        f"the glyph vanished at tier {tier}",
                    )

    def test_no_state_is_distinguishable_by_color_alone_at_any_tier(self):
        """The invariant stated as the property that matters: strip color, keep the meaning.

        For every pair of fixture rows that CARRY DIFFERENT STAGES, the rows must still differ once
        every escape is stripped. If two rows became identical without color, then at that tier
        color would be the sole carrier of the distinction, which R9.3a.5 forbids.
        """
        for tier in (T.DEPTH_256, T.DEPTH_16, T.DEPTH_NONE):
            rows = self._render(tier)
            for i, (stage_a, _native_a, line_a) in enumerate(rows):
                for stage_b, _native_b, line_b in rows[i + 1 :]:
                    if stage_a == stage_b:
                        continue
                    with self.subTest(tier=tier, a=stage_a, b=stage_b):
                        self.assertNotEqual(
                            T.strip_ansi(line_a),
                            T.strip_ansi(line_b),
                            f"{stage_a} and {stage_b} are distinguishable only by color at "
                            f"tier {tier}",
                        )

    def test_the_none_tier_emits_no_escape_at_all(self):
        for _stage, _native, line in self._render(T.DEPTH_NONE):
            self.assertEqual(line, T.strip_ansi(line))

    def test_the_two_colored_tiers_do_emit_escapes(self):
        """Guard the guard: if both colored tiers silently emitted plain text, the invariant
        tests above would pass trivially and prove nothing."""
        for tier in (T.DEPTH_256, T.DEPTH_16):
            for _stage, _native, line in self._render(tier):
                self.assertNotEqual(line, T.strip_ansi(line), f"tier {tier} was plain")

    def test_the_collapsed_stages_remain_separable_without_color(self):
        """The collapses are only ACCEPTABLE because the glyph still separates them (R9.3a.5).

        This is the test that justifies the collapses rather than merely recording them: at 16-color
        the six active stages share one code, so if their glyphs also matched, the tier really would
        lose information.
        """
        for group in T.EXPECTED_16_COLOR_COLLAPSES:
            glyphs = {LS.STAGES[stage].unicode for stage in group}
            shared_color = {T.color_16_for_stage(stage) for stage in group}
            self.assertEqual(len(shared_color), 1)
            self.assertEqual(
                len(glyphs),
                len(group),
                f"stages {group} share a 16-color code AND a glyph, so the collapse loses "
                f"information; glyphs were {glyphs}",
            )


class ColorDepthConfigContractTests(_DepthTestBase):
    """A12c, from the `term` side: the config enum and the resolver cannot drift apart."""

    def test_the_config_enum_matches_the_resolver_ladder_exactly(self):
        """`config` duplicates the three tier literals to avoid an import cycle (term -> config).

        This assertion is what makes that duplication safe: the two lists must be identical, in the
        same order, so a fourth tier added to one is a loud failure rather than a key the user can
        set but the resolver ignores.
        """
        self.assertEqual(tuple(CFG.COLOR_DEPTH_VALUES), tuple(T.COLOR_DEPTHS))

    def test_every_accepted_value_is_actually_honored_by_the_resolver(self):
        """Totality: each value `aw config` accepts must resolve to that same tier."""
        self._capable_tty()
        for value in CFG.COLOR_DEPTH_VALUES:
            with self.subTest(pin=value):
                self._pin(value)
                self.assertEqual(T.resolve_color_depth(_FakeTTY()), value)


# ==========================================================================================
# The lifecycle rendering boundary (spec `uonrjg` R10.2, Sections 9.1 / 9.2 / 9.4; plan bn026f)
# ==========================================================================================

#: The two Section 5 glyphs that carry U+FE0E, i.e. the two that are 2 CODE POINTS and 1 COLUMN.
#: Every width and truncation assertion below is aimed at these, because every other glyph in the
#: table passes a naive codepoint implementation and so proves nothing.
_VS_BLOCKED = "\u26a0\ufe0e"  # blocked
_VS_RECOVERING = "\u21a9\ufe0e"  # recovering
_NO_VS_READY = "\u25d5"  # ready, 1 code point and 1 column


class ResolutionIsSeparateFromRenderingTests(unittest.TestCase):
    """R10.2: the seam. Resolution returns DATA; only the renderers emit escapes.

    This is the property the previous lifecycle path did not have (`Term.status_256` resolved a
    color and emitted an escape on the next line), so these tests assert the SEAM itself rather than
    any particular color.
    """

    def test_resolve_lifecycle_returns_ansi_free_data(self):
        resolved = T.resolve_lifecycle("backlog", "blocked")
        self.assertNotIn("\033", repr(resolved))
        self.assertEqual(resolved.stage, LS.BLOCKED)
        self.assertEqual(resolved.native_status, "blocked")

    def test_resolve_lifecycle_consults_no_terminal_and_no_environment(self):
        """The resolve half must be answerable with no stream and no capability at all.

        Asserted by resolving the same input under three hostile environments and requiring a
        byte-identical answer: if resolution ever sniffed the terminal, one of these would differ.
        """
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
            self.assertEqual(len(set(answers)), 1, answers)
        finally:
            for k, v in saved.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v

    def test_term_defines_no_lifecycle_stage_table_of_its_own(self):
        """R10.1: the stage vocabulary, glyphs and fallbacks live in ONE module.

        The check is by BEHAVIOR rather than by grep: every glyph and fallback the renderer emits
        must be the one `lifecycle_style` holds, for every stage, in both modes. A private copy in
        `term.py` would have to agree with the table on all forty values to pass, at which point it
        is no longer a divergent table.
        """
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

    def test_the_word_is_always_present_so_the_glyph_is_never_the_sole_carrier(self):
        """Section 11 items 1 and 2: a lifecycle display always carries a word."""
        for resolved in (
            T.resolve_lifecycle("plans", "approved"),
            T.resolve_lifecycle("plans", "approved", activity="executing"),
            T.resolve_lifecycle("releases", "planned"),
        ):
            with self.subTest(stage=resolved.stage):
                self.assertTrue(T.lifecycle_word(resolved).strip())

    def test_the_native_word_outranks_the_stage_name_and_keeps_its_case(self):
        """Section 0: the native status is authoritative, so it is not rewritten for display."""
        resolved = T.resolve_lifecycle("specs", "Implementing")
        self.assertEqual(T.lifecycle_word(resolved), "Implementing")
        self.assertEqual(resolved.stage, LS.EXECUTING)


class FullRowStylingTests(unittest.TestCase):
    """A10 / Section 9.1: glyph, id6 and status share ONE color and weight; the rest carry none."""

    def setUp(self):
        self.term = T.Term(color=True, unicode=True, depth=T.DEPTH_256)
        self.resolved = T.resolve_lifecycle("backlog", "blocked")

    def _row(self, **kwargs):
        return self.term.format_lifecycle_row(self.resolved, **kwargs)

    def test_the_three_lifecycle_cells_carry_the_same_code_and_weight(self):
        row = self._row(
            id6="abc123", artifact_type="BACKLOG", title="Short title", path="a/b.md"
        )
        codes = _ANSI.findall(row)
        opens = [c for c in codes if c != "\033[0m"]
        self.assertEqual(
            len(opens),
            3,
            f"expected exactly three styled cells, got {opens!r} in {row!r}",
        )
        self.assertEqual(len(set(opens)), 1, f"the three cells disagree: {opens!r}")
        expected = f"\033[1;38;5;{LS.style_for(LS.BLOCKED).color}m"
        self.assertEqual(opens[0], expected)

    def test_the_type_title_and_path_carry_no_escape_at_all(self):
        row = self._row(
            id6="abc123", artifact_type="BACKLOG", title="Short title", path="a/b.md"
        )
        for neutral in ("BACKLOG", "Short title", "a/b.md"):
            with self.subTest(cell=neutral):
                idx = row.index(neutral)
                self.assertNotIn(
                    "\033", row[idx : idx + len(neutral)], f"{neutral!r} was styled"
                )

    def test_whole_row_coloring_is_unreachable_through_the_api(self):
        """THE NEGATIVE CASE. A10 asserted only positively cannot catch a regression to whole-row
        coloring, so this asserts the API offers no parameter by which a caller could ask for it."""
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
        # And the structural guarantee: the number of styled runs does not grow with the number of
        # neutral cells supplied.
        bare = _ANSI.findall(self._row(id6="abc123"))
        full = _ANSI.findall(
            self._row(
                id6="abc123",
                artifact_type="BACKLOG",
                title="Short title",
                path="a/b.md",
            )
        )
        self.assertEqual(len(bare), len(full))

    def test_an_unbolded_stage_is_rendered_without_the_bold_prefix(self):
        """The bold flag is the TABLE's, not the renderer's (Section 11 item 4)."""
        resolved = T.resolve_lifecycle("plans", "draft")  # formative, bold=False
        self.assertFalse(resolved.style.bold)
        row = self.term.format_lifecycle_row(resolved, id6="abc123")
        self.assertIn(f"\033[38;5;{resolved.style.color}m", row)
        self.assertNotIn("\033[1;", row)

    def test_the_glyph_immediately_precedes_the_id6(self):
        """Section 9.1: the glyph's referent must be unambiguous."""
        plain = T.strip_ansi(self._row(id6="abc123", artifact_type="BACKLOG"))
        self.assertRegex(plain, r"\u26a0\ufe0e\s+abc123")

    def test_no_row_column_is_measured_in_code_points(self):
        """Section 9.4 bullet 4, asserted through the row API: two rows whose only difference is a
        VS-bearing versus a non-VS glyph must occupy the SAME visible width."""
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
        self.assertIn(_VS_BLOCKED, blocked)
        self.assertEqual(
            T.visible_width(blocked.split("abc123")[0]),
            T.visible_width(ready.split("abc123")[0]),
        )


class CompactFormAndLegendTests(unittest.TestCase):
    """Section 9.2: the compact `GLYPH id6` form and the GENERATED legend renderer."""

    def setUp(self):
        self.term = T.Term(color=True, unicode=True, depth=T.DEPTH_256)

    def test_the_glyph_and_id6_are_styled_as_separate_tokens_not_one_run(self):
        """The glyph and id6 share the same lifecycle color and weight, but are emitted
        as separate SGR tokens to prevent terminal text shapers from coalescing font fallback
        metrics across the glyph boundary and squishing ambiguous-width symbols."""
        resolved = T.resolve_lifecycle("backlog", "blocked")
        out = self.term.format_lifecycle_compact("abc123", resolved)
        expected = f"\033[1;38;5;208m{_VS_BLOCKED}\033[0m \033[1;38;5;208mabc123\033[0m"
        self.assertEqual(out, expected, repr(out))

    def test_the_compact_form_communicates_the_stage_without_color(self):
        """A compact id6-only view must still carry the state in monochrome."""
        plain = T.Term(color=False, unicode=True)
        seen = {
            plain.format_lifecycle_compact("abc123", T.resolve_lifecycle(f, s))
            for f, s in (
                ("plans", "approved"),
                ("plans", "executed"),
                ("backlog", "blocked"),
            )
        }
        self.assertEqual(len(seen), 3, seen)

    def test_the_legend_covers_every_stage_and_is_generated_not_literal(self):
        """The row COUNT is computed from the live table at runtime, so a stage added upstream
        appears with no edit here and a hand-written literal legend could not pass."""
        lines = self.term.format_lifecycle_legend().splitlines()
        self.assertEqual(len(lines), len(LS.STAGE_ORDER))
        for stage in LS.STAGE_ORDER:
            self.assertTrue(
                any(line.endswith(stage) for line in lines), f"{stage} missing"
            )

    def test_the_legend_uses_lifecycle_order_and_not_color_order(self):
        """Section 11 item 6."""
        lines = T.strip_ansi(
            T.Term(color=False, unicode=True).format_lifecycle_legend()
        ).splitlines()
        self.assertEqual([line.split()[-1] for line in lines], list(LS.STAGE_ORDER))

    def test_the_legend_shows_the_glyph_the_ascii_fallback_and_the_word(self):
        lines = T.strip_ansi(self.term.format_lifecycle_legend()).splitlines()
        for stage, line in zip(LS.STAGE_ORDER, lines):
            style = LS.style_for(stage)
            with self.subTest(stage=stage):
                self.assertIn(style.unicode, line)
                self.assertIn(style.ascii, line)
                self.assertTrue(line.endswith(stage))

    def test_the_legend_in_ascii_mode_uses_the_exact_section_5_fallbacks(self):
        """A12: the exact Section 5 fallback, and NOTHING non-ASCII anywhere in the legend.

        Asserted as "the whole line is ASCII" rather than as "the grapheme is absent", because two
        stages (`unknown` and `parked`'s neighbours aside, concretely `unknown`) have a Unicode form
        that IS an ASCII character (`?`), so an absence assertion would fail on a conforming render.
        """
        lines = (
            T.Term(color=False, unicode=False).format_lifecycle_legend().splitlines()
        )
        self.assertEqual(len(lines), len(LS.STAGE_ORDER))
        for stage, line in zip(LS.STAGE_ORDER, lines):
            style = LS.style_for(stage)
            with self.subTest(stage=stage):
                self.assertTrue(line.startswith(style.ascii))
                self.assertTrue(line.isascii(), repr(line))
                self.assertTrue(line.endswith(stage))

    def test_the_legend_holds_no_once_per_process_latch(self):
        """The 'show once per view with 3+ stages' rule is each VIEW's judgement (child `7p3tt8`
        and the converting children). A module-level latch here would make output depend on
        invocation order and would be untestable in a shared-process suite, so calling the renderer
        repeatedly must be idempotent."""
        first = self.term.format_lifecycle_legend()
        self.assertEqual(first, self.term.format_lifecycle_legend())
        self.assertEqual(
            first,
            T.Term(
                color=True, unicode=True, depth=T.DEPTH_256
            ).format_lifecycle_legend(),
        )


class GraphemeSafetyTests(unittest.TestCase):
    """Section 9.4 / A15: an opaque grapheme, in UTF-8 mode as well as ASCII mode."""

    def test_a_variation_selector_costs_zero_columns(self):
        """Bullet 4's precondition: `len()` says 2, the terminal shows 1."""
        for glyph in (_VS_BLOCKED, _VS_RECOVERING):
            with self.subTest(glyph=repr(glyph)):
                self.assertEqual(len(glyph), 2)
                self.assertEqual(T.visible_width(glyph), 1)
        self.assertEqual(T.visible_width(_NO_VS_READY), 1)

    def test_every_multi_codepoint_glyph_the_table_declares_measures_one_column(self):
        """Asserted over `lifecycle_style.MULTI_CODEPOINT_GLYPHS` rather than over a local list, so
        a third such glyph added upstream is covered automatically."""
        for glyph in LS.MULTI_CODEPOINT_GLYPHS:
            with self.subTest(glyph=repr(glyph)):
                self.assertGreater(len(glyph), 1)
                self.assertEqual(T.visible_width(glyph), 1)

    def test_the_width_helper_is_ansi_aware(self):
        term = T.Term(color=True, unicode=True, depth=T.DEPTH_256)
        resolved = T.resolve_lifecycle("backlog", "blocked")
        styled = term.style_lifecycle_text(_VS_BLOCKED, resolved)
        self.assertIn("\033", styled)
        self.assertEqual(T.visible_width(styled), T.visible_width(_VS_BLOCKED))

    def test_a_padded_lifecycle_column_aligns_in_utf8_mode(self):
        """SECTION 9.4 BULLET 2, which no lettered criterion covers.

        The pre-change behavior this pins: `status_256('⚠︎', width=4)` produced 4 code points but 3
        rendered columns, while `status_256('◕', width=4)` produced 4 and 4, so a lifecycle column
        of mixed glyphs was ragged by exactly one column on the two VS-bearing rows.
        """
        term = T.Term(color=False, unicode=True)
        widths = {
            stage: T.visible_width(
                term.format_lifecycle_marker(
                    LS.Resolved(
                        stage=stage, style=LS.style_for(stage), family=LS.FAMILY_PLANS
                    ),
                    width=4,
                )
            )
            for stage in LS.STAGE_ORDER
        }
        self.assertEqual(set(widths.values()), {4}, widths)

    def test_the_old_codepoint_padding_really_was_ragged(self):
        """GUARD THE GUARD: if `status_256` had already been column-exact, the test above would pass
        trivially and prove nothing. This measures the defect the new path avoids."""
        legacy = T.Term(color=False)
        self.assertEqual(T.visible_width(legacy.status_256(_VS_BLOCKED, width=4)), 3)
        self.assertEqual(T.visible_width(legacy.status_256(_NO_VS_READY, width=4)), 4)

    def test_truncation_never_severs_a_variation_selector(self):
        """A15 / bullet 1, asserted AT THE ADVERSARIAL BOUNDARY.

        A naive codepoint clip passes at every offset EXCEPT the one that lands between the base
        character and its selector, so the test walks every boundary rather than picking a safe one.
        """
        text = "xxx" + _VS_BLOCKED + "tail"
        for limit in range(1, T.visible_width(text) + 1):
            out = T.truncate_visible(text, limit)
            with self.subTest(limit=limit):
                if "\u26a0" in out:
                    self.assertIn(
                        "\ufe0e",
                        out,
                        f"limit {limit} severed the selector: "
                        f"{[hex(ord(c)) for c in out]}",
                    )

    def test_truncating_a_styled_row_keeps_the_selector_attached(self):
        term = T.Term(color=True, unicode=True, depth=T.DEPTH_256)
        row = term.format_lifecycle_row(
            T.resolve_lifecycle("backlog", "blocked"),
            id6="abc123",
            artifact_type="BACKLOG",
            title="Short title",
        )
        for limit in range(1, T.visible_width(row) + 1):
            out = T.truncate_visible(row, limit)
            with self.subTest(limit=limit):
                if "\u26a0" in out:
                    self.assertIn("\ufe0e", out)
                self.assertLessEqual(T.visible_width(out), limit)

    def test_truncation_closes_a_style_it_leaves_open(self):
        """A clipped row must not leak its lifecycle color into the rest of the line."""
        term = T.Term(color=True, unicode=True, depth=T.DEPTH_256)
        row = term.format_lifecycle_row(
            T.resolve_lifecycle("backlog", "blocked"), id6="abc123"
        )
        out = T.truncate_visible(row, 4)
        self.assertTrue(out.endswith("\033[0m"), repr(out))

    def test_truncation_returns_the_text_unchanged_when_it_fits(self):
        term = T.Term(color=True, unicode=True, depth=T.DEPTH_256)
        row = term.format_lifecycle_row(
            T.resolve_lifecycle("backlog", "blocked"), id6="abc123"
        )
        self.assertEqual(T.truncate_visible(row, 500), row)

    def test_an_ellipsis_is_counted_against_the_limit_and_left_unstyled(self):
        term = T.Term(color=True, unicode=True, depth=T.DEPTH_256)
        row = term.format_lifecycle_row(
            T.resolve_lifecycle("backlog", "blocked"),
            id6="abc123",
            title="Long title here",
        )
        out = T.truncate_visible(row, 12, ellipsis="\u2026")
        self.assertLessEqual(T.visible_width(out), 12)
        self.assertTrue(out.endswith("\u2026"))
        self.assertFalse(out.endswith("\u2026\033[0m"))

    def test_ascii_mode_guarantees_single_byte_alignment(self):
        """Bullet 3: in ASCII mode every fallback is exactly one byte, so a column cannot be ragged
        at all. This is the bullet the substitution table alone satisfies."""
        term = T.Term(color=False, unicode=False)
        for stage in LS.STAGE_ORDER:
            resolved = LS.Resolved(
                stage=stage, style=LS.style_for(stage), family=LS.FAMILY_PLANS
            )
            rendered = term.format_lifecycle_marker(resolved)
            with self.subTest(stage=stage):
                self.assertTrue(rendered.isascii())
                self.assertEqual(len(rendered.encode("ascii")), 1)

    def test_no_lifecycle_render_uses_a_bare_len_for_a_visible_column(self):
        """Bullet 4 asserted as a PROPERTY rather than by grepping the source: for every stage, in
        both modes, a padded marker measures the requested number of VISIBLE columns. A `len()`-based
        pad fails this for exactly the VS-bearing stages."""
        for mode in (True, False):
            term = T.Term(color=False, unicode=mode)
            for stage in LS.STAGE_ORDER:
                resolved = LS.Resolved(
                    stage=stage, style=LS.style_for(stage), family=LS.FAMILY_PLANS
                )
                with self.subTest(stage=stage, unicode=mode):
                    self.assertEqual(
                        T.visible_width(
                            term.format_lifecycle_marker(resolved, width=6)
                        ),
                        6,
                    )

    def test_strip_ansi_preserves_the_variation_selector(self):
        """A15's stripping clause. Already true before this change; pinned so it stays true."""
        term = T.Term(color=True, unicode=True, depth=T.DEPTH_256)
        styled = term.format_lifecycle_marker(T.resolve_lifecycle("backlog", "blocked"))
        self.assertIn("\ufe0e", T.strip_ansi(styled))

    def test_the_emoji_presentation_forms_never_appear(self):
        """A5: U+FE0F must not reach output, in any mode or tier."""
        for tier in (T.DEPTH_256, T.DEPTH_16, T.DEPTH_NONE):
            for mode in (True, False):
                term = T.Term(color=tier != T.DEPTH_NONE, unicode=mode, depth=tier)
                out = term.format_lifecycle_legend()
                with self.subTest(tier=tier, unicode=mode):
                    self.assertNotIn("\ufe0f", out)


class _Utf8TTY(_FakeTTY):
    """A 256-capable UTF-8 TTY double.

    EXTENDS the shipped `_FakeTTY`/`_FakePipe` pattern rather than replacing it, for the one reason
    those two cannot cover the ASCII rung: `io.StringIO` HAS an `encoding` attribute whose value is
    `None`, and `should_unicode` treats `None` as "no information" and falls through to True. So an
    ASCII-capability profile needs an EXPLICIT encoding.

    DECLARED AS A CLASS ATTRIBUTE, not assigned in ``__init__``: ``encoding`` is read-only on an
    ``io.StringIO`` INSTANCE (``AttributeError: attribute 'encoding' of '_io._TextIOBase' objects is
    not writable``), and a class attribute on a Python subclass shadows it cleanly.
    """

    encoding = "utf-8"


class _Utf8Pipe(_FakePipe):
    encoding = "utf-8"


class _AsciiPipe(_FakePipe):
    """The rung `_FakePipe` alone cannot reach: a stream that genuinely cannot render the grapheme."""

    encoding = "ascii"


class CapabilityMatrixTests(unittest.TestCase):
    """A16: the six named environment profiles, each a DISTINCT test rather than one composite.

    Each case asserts BOTH axes, because they are independent resolvers and a profile that got one
    right and the other wrong would otherwise pass: the glyph FORM (Unicode grapheme versus the
    exact Section 5 ASCII fallback) and ANSI presence or absence.
    """

    #: One stage that is VS-bearing, so each profile also exercises the grapheme path.
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
            self.assertIn("\033[", out, f"expected ANSI in {out!r}")
        else:
            self.assertNotIn("\033", out, f"expected NO ANSI in {out!r}")
        plain = T.strip_ansi(out)
        if unicode_form:
            self.assertIn(style.unicode, plain, f"expected the grapheme in {plain!r}")
        else:
            self.assertNotIn(style.unicode, plain, f"grapheme leaked into {plain!r}")
            self.assertIn(style.ascii, plain, f"expected the fallback in {plain!r}")
        # The WORD survives every profile (Section 11 item 1, R9.3a.5).
        self.assertIn(self.NATIVE, plain)

    def test_profile_1_normal_utf8(self):
        self._assert_profile(
            self._render(_Utf8TTY()),
            ansi=True,
            unicode_form=True,
        )

    def test_profile_2_ascii_mode(self):
        os.environ["AW_ASCII_ONLY"] = "1"
        self._assert_profile(
            self._render(_Utf8TTY()),
            ansi=True,
            unicode_form=False,
        )

    def test_profile_2b_force_ascii_is_the_same_rung(self):
        os.environ["FORCE_ASCII"] = "1"
        self._assert_profile(
            self._render(_Utf8TTY()),
            ansi=True,
            unicode_form=False,
        )

    def test_profile_3_colored_tty(self):
        os.environ["TERM"] = "xterm-256color"
        out = self._render(_Utf8TTY())
        self._assert_profile(out, ansi=True, unicode_form=True)
        self.assertIn(f"38;5;{LS.style_for(self.STAGE).color}", out)

    def test_profile_4_plain_tty(self):
        """A TTY with color explicitly suppressed: glyph and word remain, no escape (A11)."""
        os.environ["NO_COLOR"] = "1"
        self._assert_profile(
            self._render(_Utf8TTY()),
            ansi=False,
            unicode_form=True,
        )

    def test_profile_5_piped_output(self):
        self._assert_profile(
            self._render(_Utf8Pipe()),
            ansi=False,
            unicode_form=True,
        )

    def test_profile_6_term_dumb(self):
        os.environ["TERM"] = "dumb"
        self._assert_profile(
            self._render(_Utf8TTY()),
            ansi=False,
            unicode_form=True,
        )

    def test_a13_force_color_enables_ansi_on_a_pipe(self):
        """A13(a): `FORCE_COLOR=1` with no flag beats TTY detection."""
        os.environ["FORCE_COLOR"] = "1"
        self._assert_profile(
            self._render(_Utf8Pipe()),
            ansi=True,
            unicode_form=True,
        )

    def test_a13_force_color_does_not_force_unicode_onto_an_ascii_stream(self):
        """A13's ASCII half, as its OWN named case: ANSI present AND the fallback used.

        A CHARACTERIZATION TEST of shipped behavior (`should_unicode` never reads `FORCE_COLOR`),
        written so that a later change COUPLING the two resolvers fails here.
        """
        os.environ["FORCE_COLOR"] = "1"
        out = self._render(_AsciiPipe())
        self._assert_profile(out, ansi=True, unicode_form=False)

    def test_a13_the_no_color_flag_beats_force_color(self):
        """A13(b): the flag layer is above the environment."""
        os.environ["FORCE_COLOR"] = "1"
        T.set_color_override(False)
        self._assert_profile(
            self._render(_Utf8TTY()),
            ansi=False,
            unicode_form=True,
        )

    def test_a13_a_falsey_force_color_neither_forces_nor_suppresses(self):
        """A13(c): `FORCE_COLOR=0` on a pipe stays monochrome."""
        os.environ["FORCE_COLOR"] = "0"
        self._assert_profile(
            self._render(_Utf8Pipe()),
            ansi=False,
            unicode_form=True,
        )

    def test_the_sixteen_color_tier_renders_from_the_authored_palette(self):
        """The depth ladder reaches the lifecycle renderer, not just the resolver."""
        os.environ["TERM"] = "xterm-color"
        out = self._render(_Utf8TTY())
        self.assertIn(f"\033[1;{T.color_16_for_stage(self.STAGE)}m", out)
        self.assertNotIn("38;5;", out)


if __name__ == "__main__":
    unittest.main()
