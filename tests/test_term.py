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
