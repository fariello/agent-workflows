#!/usr/bin/env python3

"""THE UNIFORMITY GATE for the CLI presentation-override flags (ttyflags `yaxr4i` E-04/E-08).

WHAT THIS FILE IS FOR, since the individual flag assertions are the least interesting part of it.
The presentation flags were INCONSISTENT PER COMMAND, which is worse than uniformly absent because
it cannot be scripted around: `aw attention --no-color` worked while `aw oc run --no-color` was a
usage error, and the gap landed exactly on the long-running driver commands whose output an operator
most wants to capture in a log.

THE GAP WAS ACTIVELY REGROWING, which is why a RECURSIVE WALK is the durable deliverable rather than
the flag additions themselves. Measured three times: backlog item `isg0kg` found `--no-color` missing
on 18 of 175 nested subcommands; the plan re-measured 25 of 219; this implementation measured 29 of
229. Each newly-missing leaf (`run as`, `run ipd`, the `review` leaves, then the `integrate` leaves)
was a command added AFTER the previous count, having missed the shared parent as it landed. A
per-command spot check demonstrably did not catch that, three times running. A recursive walk does.

WHY A DECLARED-SURFACE TEST AND A BEHAVIORAL TEST ARE BOTH HERE, because neither alone is sufficient
and that is the load-bearing lesson of this work. The plan specified adding `parents=[common]` to the
leaves missing it, and measurement showed THAT ALONE DOES NOT WORK: 11 of the missing parser objects
are host-driver leaves whose argv `cli._dispatch` intercepts and forwards VERBATIM to another
program's parser BEFORE `parse_args` runs, so a flag declared on the leaf is never consulted. With
`parents=[common]` applied and nothing else, `aw oc run --no-color status` still exited 2 with
`runipd: error: unrecognized arguments: --no-color`. So:

  * :class:`DeclaredFlagSurfaceTests` walks the parser tree and asserts the DECLARED surface, which
    is what makes `--help` honest and what catches a new leaf that forgot the shared parent.
  * :class:`ForwardedPathBehaviorTests` drives the actual dispatch path and asserts the flags are
    CONSUMED there, which is the only thing that proves they work on the forwarded leaves.

A test asserting only the first would have passed against a build where the flag was still a usage
error on nine commands.
"""

from __future__ import annotations

import argparse
import io
import os
import unittest
from typing import Dict, List, Sequence, Tuple

from agent_workflows import cli, term


#: The presentation flags every non-hidden subcommand must accept.
PRESENTATION_FLAGS = ("--no-color", "--color", "--agent", "--json")

#: THE EXEMPTION LIST, as a CLOSED NAMED SET rather than a predicate (E-08).
#:
#: A predicate such as "skip anything hidden" would SILENTLY ABSORB the next hidden or newly added
#: subcommand, which is precisely the regrowth this file exists to stop: the gap grew 18 -> 25 -> 29
#: exactly because new leaves inherited nothing and nobody was forced to notice. A closed list makes
#: the next flagless command FAIL until a human decides about it.
#:
#: `__complete` is the hidden shell-completion query (`aw __complete --cword N -- <tokens>`). It is
#: exempt because it is not a human-facing verb: it is invoked by the shell, its entire output is a
#: newline-delimited candidate list, and it always exits 0 so a completion query never errors the
#: shell. Styling flags would be meaningless on it.
EXEMPT_SUBCOMMANDS = frozenset({"__complete"})

#: THE FORWARDED LEAVES: subcommands that DELIBERATELY declare no flags of their own, whose color
#: flags are honored by CONSUMPTION in `cli._dispatch` instead of by declaration.
#:
#: WHY THIS IS A SECOND CATEGORY AND NOT A SECOND EXEMPTION. These commands DO accept `--color` and
#: `--no-color`; they simply do not DECLARE them, and the distinction is forced by a pre-existing
#: contract rather than chosen here. Each forwards its whole argv VERBATIM to another program's
#: parser, which must own every flag and its `--help`, so that `aw run as gem X` cannot drift from
#: `aw oc run as gem X`. `tests/test_run_dispatch.py`
#: (`test_each_added_route_owns_no_flags_and_declares_its_contract`) asserts a route declares ZERO
#: flags, and `aw oc run --help` renders the DRIVER's help, not `cli`'s, so a declaration here would
#: be invisible decoration that also breaks that test. Measured both ways during this work.
#:
#: SO THE CONTRACT FOR THESE IS BEHAVIORAL, and :class:`ForwardedPathBehaviorTests` is where it is
#: enforced: the flag must be CONSUMED before forwarding, which is what keeps it from reaching a
#: downstream parser as `unrecognized arguments`. That behavioral test is the load-bearing one for
#: this group; listing them here only records WHY the declared-surface check skips them.
#:
#: `--agent`/`--json` are deliberately NOT provided on these, by declaration or by consumption: `aw`
#: does not render their output, and on `aw oc run start` a downstream `--agent` is an OpenCode AGENT
#: NAME rather than a machine-output flag, so honoring it here would change what the operator meant.
FORWARDED_SUBCOMMANDS = frozenset(
    {
        "run as",
        "run ipd",
        "oc runipd",
        "oc run",
        "oc review",
        "oc integrate",
        "opencode runipd",
        "opencode run",
        "opencode review",
        "opencode integrate",
        "agy runipd",
        "agy run",
        "agy runagy",
        "agy review",
        "agy integrate",
        "agy sessions",
        "agy view",
        "agy view-antigravity-jsonl",
        "agy exec",
        "antigravity runipd",
        "antigravity run",
        "antigravity runagy",
        "antigravity review",
        "antigravity integrate",
        "antigravity sessions",
        "antigravity view",
        "antigravity view-antigravity-jsonl",
        "antigravity exec",
    }
)


def _walk_subcommands(
    parser: argparse.ArgumentParser,
) -> List[Tuple[str, argparse.ArgumentParser]]:
    """Every subcommand in the tree, nested included, as (dotted-name, parser) pairs.

    RECURSIVE BY CONSTRUCTION: it descends into every `argparse._SubParsersAction.choices`, so a
    leaf three levels down (`aw ipd dependencies set`) is visited exactly like a top-level verb.
    That is the whole point; a flat scan of the top level is what missed the nested gaps.
    """

    found: List[Tuple[str, argparse.ArgumentParser]] = []

    def visit(node: argparse.ArgumentParser, path: Sequence[str]) -> None:
        if path:
            found.append((" ".join(path), node))
        for action in node._actions:
            if isinstance(action, argparse._SubParsersAction):
                for name, sub in action.choices.items():
                    visit(sub, [*path, name])

    visit(parser, [])
    return found


def _declares(parser: argparse.ArgumentParser, flag: str) -> bool:
    return any(flag in (action.option_strings or []) for action in parser._actions)


class DeclaredFlagSurfaceTests(unittest.TestCase):
    """The DECLARED surface: every non-hidden subcommand registers every presentation flag."""

    def setUp(self) -> None:
        self.subcommands = _walk_subcommands(cli._build_parser())

    def test_the_walk_sees_a_deep_tree_not_just_top_level_verbs(self):
        """Guard the INSTRUMENT before trusting its verdict.

        A walk that silently stopped at depth 1 would report a clean surface for the nested leaves
        that actually regressed, so this asserts the walk observes a plausibly large tree AND
        reaches a known deep leaf. Deliberately a LOWER BOUND rather than an exact count: the
        subcommand total grows every time a verb is added (175 -> 219 -> 229 across three
        measurements of this same gap), and an exact count would be a tripwire on unrelated work.
        """

        names = {name for name, _ in self.subcommands}
        self.assertGreater(
            len(names),
            150,
            f"the parser walk found only {len(names)} subcommands, which suggests it stopped "
            "descending rather than that the CLI shrank",
        )
        self.assertIn(
            "ipd dependencies set", names, "walk did not reach a depth-3 leaf"
        )
        self.assertIn("oc run", names, "walk did not reach the host-driver leaves")

    def test_every_non_hidden_subcommand_declares_every_presentation_flag(self):
        """THE LOAD-BEARING ASSERTION of this file.

        Reports EVERY (subcommand, flag) cell that is missing, in one failure, rather than dying on
        the first: "one leaf forgot the parent" and "a whole family forgot it" are different
        defects, and a reader needs the shape of the gap to tell them apart.
        """

        missing: Dict[str, List[str]] = {}
        for name, parser in self.subcommands:
            if name in EXEMPT_SUBCOMMANDS or name in FORWARDED_SUBCOMMANDS:
                continue
            absent = [f for f in PRESENTATION_FLAGS if not _declares(parser, f)]
            if absent:
                missing[name] = absent

        self.assertEqual(
            missing,
            {},
            "subcommand(s) do not accept the presentation flags. Add `parents=[common]` to each "
            "registration in `cli._build_parser`. If a command is deliberately exempt, add it to "
            "EXEMPT_SUBCOMMANDS (hidden/non-human verbs) or FORWARDED_SUBCOMMANDS (verbatim argv "
            f"forwarding, where the flag is consumed instead) with the reason. Missing: {missing}",
        )

    def test_the_forwarded_leaves_declare_no_flags_as_their_own_contract_requires(self):
        """The forwarded group's declared surface is asserted to be EMPTY of these flags, not full.

        Stated as a POSITIVE assertion so the skip above cannot rot into a blanket pass. If someone
        later adds `parents=[common]` to one of these, THIS fails and points at
        `tests/test_run_dispatch.py`, which independently requires a route to own zero flags. The
        two tests then agree instead of fighting, and nobody has to rediscover that
        `aw oc run --help` renders the driver's help rather than `cli`'s.
        """

        by_name = dict(self.subcommands)
        offenders = {}
        for name in sorted(FORWARDED_SUBCOMMANDS):
            parser = by_name.get(name)
            if parser is None:
                offenders[name] = "no longer a subcommand; remove the stale entry"
                continue
            declared = [f for f in PRESENTATION_FLAGS if _declares(parser, f)]
            if declared:
                offenders[name] = (
                    f"declares {declared}; a verbatim-forwarding leaf must own NO flags so the "
                    "downstream parser owns every flag and its --help"
                )
        self.assertEqual(offenders, {}, f"forwarded-leaf contract broken: {offenders}")

    def test_the_exemption_is_a_closed_named_set_and_is_minimal(self):
        """E-08: the exemption must be a NAMED set, and every name in it must still exist.

        A stale exemption is as dangerous as a missing one: it reads as a deliberate decision about
        a command that may have been renamed away, so the next flagless command inherits a pass.
        """

        self.assertIsInstance(EXEMPT_SUBCOMMANDS, frozenset)
        names = {name for name, _ in self.subcommands}
        for exempt in EXEMPT_SUBCOMMANDS:
            self.assertIn(
                exempt,
                names,
                f"EXEMPT_SUBCOMMANDS names {exempt!r}, which is no longer a subcommand; remove the "
                "stale exemption rather than leaving it to absorb a future command",
            )

    def test_an_unlisted_flagless_subcommand_fails_the_gate(self):
        """THE MUTATION CHECK (E-08). A guard that cannot fail proves nothing.

        Builds the real parser, grafts on a flagless subcommand that is NOT in the exemption list,
        and asserts the gate's own predicate rejects it BY NAME. This is why the exemption is a
        gate rather than a hole: it does not reach for "hidden" or any other property the new
        command could accidentally satisfy.
        """

        parser = cli._build_parser()
        subparsers_action = next(
            a for a in parser._actions if isinstance(a, argparse._SubParsersAction)
        )
        subparsers_action.add_parser(
            "zz-mutation-probe", help="flagless probe added by the mutation check"
        )

        missing = {
            name: [f for f in PRESENTATION_FLAGS if not _declares(sub, f)]
            for name, sub in _walk_subcommands(parser)
            if name not in EXEMPT_SUBCOMMANDS
            and name not in FORWARDED_SUBCOMMANDS
            and any(not _declares(sub, f) for f in PRESENTATION_FLAGS)
        }

        self.assertIn(
            "zz-mutation-probe",
            missing,
            "the uniformity gate did NOT notice an unlisted flagless subcommand, so it is "
            "decoration rather than a gate",
        )
        self.assertEqual(
            sorted(missing["zz-mutation-probe"]),
            sorted(PRESENTATION_FLAGS),
            "the gate noticed the probe but misreported which flags it lacks",
        )
        # And the ONLY offender is the probe: the real tree is clean, so the mutation is what
        # produced the failure rather than a pre-existing gap masking it.
        self.assertEqual(
            sorted(missing),
            ["zz-mutation-probe"],
            f"expected only the probe to fail, got {sorted(missing)}",
        )


class ColorFlagMutualExclusionTests(unittest.TestCase):
    """`--color` with `--no-color` is a USAGE ERROR with exit 2 (OQ-02), never a silent winner."""

    def test_passing_both_flags_exits_two_on_a_parsed_command(self):
        parser = cli._build_parser()
        with self.assertRaises(SystemExit) as caught:
            with _swallow_stderr():
                parser.parse_args(["attention", "--no-color", "--color"])
        self.assertEqual(caught.exception.code, 2)

    def test_passing_both_flags_exits_two_on_a_forwarded_command(self):
        """The forwarded leaves never reach the mutually exclusive group, so they need their own
        refusal, and it must be the SAME exit code. A silent winner here would make `aw oc run`
        behave differently from `aw attention` for identical argv."""

        with _swallow_stderr():
            rc = cli._dispatch(["oc", "run", "--no-color", "--color", "status"])
        self.assertEqual(rc, 2)

    def test_each_flag_alone_is_accepted(self):
        parser = cli._build_parser()
        for flag, expected in (("--no-color", False), ("--color", True)):
            with self.subTest(flag=flag):
                args = parser.parse_args(["attention", flag])
                self.assertEqual(term.color_override(args), expected)


class ForwardedPathBehaviorTests(unittest.TestCase):
    """The BEHAVIORAL half: the color flags are consumed before verbatim forwarding.

    This is the half a declared-surface test cannot provide. Every command asserted here forwards
    its argv to a DIFFERENT program's parser, which declares no color flag, so if `aw` did not
    consume the token first the invocation would die with `unrecognized arguments`.
    """

    FORWARDED_COMMANDS = (
        ["oc", "run"],
        ["opencode", "run"],
        ["oc", "runipd"],
        ["agy", "run"],
        ["antigravity", "runagy"],
        ["oc", "review"],
        ["agy", "integrate"],
        ["run", "as"],
        ["run", "ipd"],
        ["agy", "sessions"],
        ["agy", "view"],
        ["agy", "exec"],
    )

    def test_color_flags_are_stripped_from_every_forwarded_argv(self):
        for prefix in self.FORWARDED_COMMANDS:
            for flag in ("--no-color", "--color"):
                with self.subTest(command=" ".join(prefix), flag=flag):
                    kept, found = cli._consume_presentation_flags(
                        [*prefix, flag, "status"]
                    )
                    self.assertEqual(
                        kept,
                        [*prefix, "status"],
                        "the color flag survived into the argv forwarded to another parser, "
                        "where it becomes `unrecognized arguments`",
                    )
                    self.assertEqual(found.override, flag == "--color")

    def test_tokens_after_a_bare_double_dash_are_left_alone(self):
        """`--` means "everything after this is data". `aw oc run -- as` is the documented way to
        pass the LITERAL selector `as`, so consuming a later `--color` would corrupt an operand."""

        kept, found = cli._consume_presentation_flags(
            ["oc", "run", "--", "--color", "as"]
        )
        self.assertEqual(kept, ["oc", "run", "--", "--color", "as"])
        self.assertIsNone(found.override)
        self.assertFalse(found.saw_color)

    def test_an_unrelated_flag_is_never_consumed(self):
        """The strip is exactly two tokens wide. `--agent` in particular MUST survive: on
        `aw oc run start` it is an OpenCode AGENT NAME, not a machine-output flag, so stealing it
        here would silently drop a downstream option's value."""

        argv = ["oc", "run", "start", "--agent", "build", "--json", "--model", "x"]
        kept, found = cli._consume_presentation_flags(argv)
        self.assertEqual(kept, argv)
        self.assertIsNone(found.override)


class ColorOverridePrecedenceTests(unittest.TestCase):
    """E-03: flag beats env beats detection, asserted in BOTH conflict directions."""

    def setUp(self) -> None:
        self._saved = {
            k: os.environ.get(k) for k in ("NO_COLOR", "FORCE_COLOR", "TERM")
        }
        for key in ("NO_COLOR", "FORCE_COLOR"):
            os.environ.pop(key, None)
        os.environ["TERM"] = "xterm-256color"
        self.addCleanup(self._restore)
        self.addCleanup(term.set_color_override, None)

    def _restore(self) -> None:
        for key, value in self._saved.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    def test_flag_beats_env_in_both_directions(self):
        os.environ["NO_COLOR"] = "1"
        self.assertTrue(term.should_color(_FakePipe(), override=True))
        os.environ.pop("NO_COLOR")
        os.environ["FORCE_COLOR"] = "1"
        self.assertFalse(term.should_color(_FakeTTY(), override=False))

    def test_env_beats_detection_when_no_flag_is_passed(self):
        os.environ["FORCE_COLOR"] = "1"
        self.assertTrue(term.should_color(_FakePipe()))

    def test_detection_alone_decides_with_neither_flag_nor_env(self):
        self.assertTrue(term.should_color(_FakeTTY()))
        self.assertFalse(term.should_color(_FakePipe()))

    def test_the_process_wide_override_is_honored_and_resettable(self):
        """The override must RESET, not accumulate: `cli._dispatch` sets it unconditionally so a
        later flagless invocation in the same process does not inherit an earlier one's choice."""

        term.set_color_override(True)
        self.assertTrue(term.should_color(_FakePipe()))
        term.set_color_override(None)
        self.assertFalse(term.should_color(_FakePipe()))

    def test_an_explicit_argument_beats_the_process_wide_value(self):
        term.set_color_override(True)
        self.assertFalse(term.should_color(_FakeTTY(), override=False))

    def test_no_color_flag_never_reaches_the_engine_through_the_environment(self):
        """A flag must not mutate `os.environ`: this package spawns nested `aw` processes, which
        would INHERIT the variable and have their output restyled by a parent's terminal choice."""

        before = dict(os.environ)
        term.set_color_override(True)
        term.should_color(_FakePipe())
        self.assertEqual(
            {k: v for k, v in os.environ.items() if k in ("NO_COLOR", "FORCE_COLOR")},
            {k: v for k, v in before.items() if k in ("NO_COLOR", "FORCE_COLOR")},
        )


class _FakeTTY(io.StringIO):
    def isatty(self) -> bool:
        return True


class _FakePipe(io.StringIO):
    def isatty(self) -> bool:
        return False


class _swallow_stderr:
    """Silence argparse's usage text so a deliberate exit-2 assertion does not spam the run."""

    def __enter__(self):
        import sys

        self._saved = sys.stderr
        sys.stderr = io.StringIO()
        return self

    def __exit__(self, *exc):
        import sys

        sys.stderr = self._saved
        return False


if __name__ == "__main__":
    unittest.main()
