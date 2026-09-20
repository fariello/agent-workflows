"""Tests for agent_workflows.term accessible styling (IPD-2 Batch D; AC-15)."""

from __future__ import annotations

import contextlib
import io
import os
import re
import tempfile
import textwrap
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

    def test_both_force_color_read_sites_agree_by_construction(self):
        """The STRUCTURAL property, not merely the behavioral one.

        `should_color` must consult `FORCE_COLOR` twice (once to decide whether it cancels
        `NO_COLOR`, once to decide whether it forces past TTY detection). Those two reads
        were INDEPENDENT before this plan - presence at one site, truthiness at the other -
        which is the contradiction that let a falsey value cancel `NO_COLOR` while failing
        to force. Asserting both reads go through ONE predicate is what keeps them moving
        together; a behavioral test alone would pass for a second, separately-written
        falsey check at each site, which would reopen the same split.
        """
        import ast
        import inspect
        import textwrap

        source = textwrap.dedent(inspect.getsource(T.should_color))
        tree = ast.parse(source)
        reads = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Constant) and node.value == "FORCE_COLOR"
        ]
        self.assertEqual(
            reads,
            [],
            "`should_color` must not name FORCE_COLOR directly; both readings belong to "
            "the single forcing predicate",
        )
        calls = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "_force_color_is_forcing"
        ]
        self.assertEqual(
            len(calls),
            2,
            "both FORCE_COLOR readings must consult the single forcing predicate",
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

    def test_the_delegation_predicate_refuses_a_body_with_logic(self):
        """Guard the guard: a predicate that called everything a delegation would make the
        test above vacuous and would wave a genuine third implementation through."""
        import ast

        fork = ast.parse(
            "def should_color(stream=None):\n"
            "    import os\n"
            "    if os.environ.get('FORCE_COLOR'):\n"
            "        return True\n"
            "    return bool(stream and stream.isatty())\n"
        ).body[0]
        self.assertFalse(
            self._is_pure_delegation(fork),
            "a body carrying its own environment logic must NOT count as a delegation",
        )
        delegation = ast.parse(
            "def should_color(stream=None):\n"
            "    '''doc'''\n"
            "    from agent_workflows import term\n"
            "    return term.should_color(stream)\n"
        ).body[0]
        self.assertTrue(
            self._is_pure_delegation(delegation),
            "the sanctioned wrapper shape (docstring + function-local import + one "
            "delegating return) must count as a delegation",
        )
        # AND THE IMPORT SUBTRACTION MUST NOT BECOME A LOOPHOLE: a body that imports and
        # then does its own work is still a fork.
        import_plus_logic = ast.parse(
            "def should_color(stream=None):\n"
            "    import os\n"
            "    if os.environ.get('NO_COLOR') is not None:\n"
            "        return False\n"
            "    return term.should_color(stream)\n"
        ).body[0]
        self.assertFalse(
            self._is_pure_delegation(import_plus_logic),
            "subtracting the import must not let a body with real logic pass as a wrapper",
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

    def test_exactly_one_definition_of_the_depth_resolver_in_the_package(self):
        import ast

        sites = []
        for path in sorted(self._package_dir().glob("*.py")):
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"))
            except SyntaxError:  # pragma: no cover - a broken module is another failure
                continue
            for node in ast.walk(tree):
                if (
                    isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and node.name == self.SYMBOL
                ):
                    sites.append(f"{path.name}:{node.lineno}")
        self.assertEqual(
            len(sites),
            1,
            "R9.3a.2 requires exactly ONE definition of the color-depth resolver; found: "
            + ", ".join(sites),
        )
        self.assertTrue(sites[0].startswith("term.py"), sites)

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

    def test_the_resolver_does_not_reimplement_the_color_decision(self):
        """The top rung must DELEGATE to `should_color`, not re-read the environment.

        Measured structurally: `resolve_color_depth`'s own body calls `should_color` and contains no
        `NO_COLOR`/`FORCE_COLOR`/`isatty` test of its own. Re-implementing those would create the
        second originating definition of the COLOR decision that `OneOriginatingDefinitionTests`
        exists to prevent, and would silently drop `--no-color` (which never reaches os.environ).
        """
        import ast
        import inspect

        source = inspect.getsource(T.resolve_color_depth)
        tree = ast.parse(textwrap.dedent(source))
        calls = {
            node.func.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
        self.assertIn(
            "should_color",
            calls,
            "the depth resolver must delegate its top rung to should_color",
        )
        body = source.split('"""', 2)[-1]
        for forbidden in ("NO_COLOR", "FORCE_COLOR", "isatty"):
            self.assertNotIn(
                forbidden,
                body,
                f"the depth resolver re-implements {forbidden} instead of delegating to "
                "should_color; that is a second originating definition of the color decision",
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


if __name__ == "__main__":
    unittest.main()
