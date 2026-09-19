#!/usr/bin/env python3
"""rununify Order 10 (`s16omw`) E-05: GUARD what this plan MEASURED, and pin what it did NOT do.

WHAT THIS PLAN DID AND DID NOT DO, stated first so no reader mistakes the shape of this file. Plan
`s16omw` is named "split `build_parser` into a shared core and a thin host hook". It did NOT perform
that split. Its own 2026-09-16 review measured why; re-measurement at execution HEAD `4a1bb873`
confirmed the shape of the finding and MOVED SEVERAL OF THE NUMBERS, which is recorded below rather
than smoothed over.

`build_parser` is the LEAST shared of this Set's five large functions, and it is the one whose
duplication is most genuinely intentional. Measured: 46 oc against 47 agy normalized code lines,
only 23 of them identical, SequenceMatcher similarity 0.4946 (against 0.851 for `execute_item` and
0.9345 for `initialize_run`). Half of each function BY CHARACTER is help text (52.1% on oc, 42.0% on
agy) documenting capabilities the other host does not have.

THE MEASUREMENT THAT MOVED, and why both numbers are true. The review recorded the flag surface as
17 shared / 7 oc-only / 10 agy-only. That is a count of option-string LITERALS written inside each
`build_parser`, and it reproduces exactly by that method. But it is not what an operator meets,
because it cannot see a `--no-X` that `argparse.BooleanOptionalAction` auto-generates, nor any flag a
shared helper registers. Counted on the LIVE parser objects the partition is 51 shared / 8 oc-only /
8 agy-only. Both are pinned below, by the method that produced each, because the literal count is
what a source-level de-duplication changes and the live count is what an operator experiences.

AND THE ECONOMICS INVERT THE PLAN'S OWN CONCERN. Of the 51 shared live option strings, 21 are
already registered from ONE place: `runner_shared.register_run_policy_flags`, twelve spec-governed
`RUN_POLICY_FLAGS` rows, called twice per host. So the spec-governed half of the shared surface is
already single-implementation, and the residual de-duplication payoff of relocating this function is
the 23 identical normalized lines this file pins. The Concern's claim that "most of the divergence is
DRIFT in shared logic" is FALSE for this symbol, and the plan's own F-1 says the opposite and is
correct.

ONE DIFFERENCE IS AN INCOMPATIBLE CONTRACT RATHER THAN DRIFT, which is why the Set's "resolve to the
oc version" ruling cannot be applied here: `--no-verify` resolves to dest `validate` on oc and
`no_verify` on agy, and `--verify`/`--audit` do not exist on agy at all. That asymmetry is pinned in
the companion characterization file (folded into THIS file by `7ebc2964`), together with the proof
that a naive oc-preferred registration RAISES at parser build time.

SO SOME ASSERTIONS BELOW ARE DELIBERATELY INVERSE: they assert a symbol is STILL defined twice and
that neither host yet delegates. That is not an endorsement of the duplication. It is a tripwire, so
a later agent cannot "finish" the split piecemeal without coming here, reading the measurement, and
updating this file deliberately. A test asserting a state the code is not in would be a failing
test, not a guard, which is why the split-side assertions are ABSENT rather than written and skipped.

WHEN THE SPLIT IS PERFORMED, this file is the checklist: each `STILL_DOUBLE_DEFINED` entry that
becomes shared moves out of that tuple in the SAME change that shares it with the reason recorded,
the two literal/live partitions are re-measured, and the residual-payoff figure is updated. That is
the "re-base deliberately, never weaken silently" rule the maintainer set on 2026-09-16.

WHY THERE IS NO SOURCE-TEXT PIN ANYWHERE IN THIS FILE beyond the AST census that IS the subject of
the assertion: measured at execution HEAD, `build_parser` carries ZERO source-inspection pins, alone
among this Set's five large functions (`execute_item` carries 14, `initialize_run` 11). All 35 test
files that touch it call `build_parser()` and assert on the parser object. Introducing the first
source pin this function has ever had would be a self-inflicted obstacle to the relocation this Set
exists to perform.
"""

from __future__ import annotations

import argparse
import ast
import builtins
import inspect
import unittest
from pathlib import Path

from agent_workflows import agy_runipd, oc_runipd, runner_shared

AW = Path(inspect.getfile(runner_shared)).parent

HOSTS = {"oc": oc_runipd, "agy": agy_runipd}
HOST_MODULE = {"oc": "oc_runipd", "agy": "agy_runipd"}

#: E-01(b): the SEVEN module-level names `oc_runipd.build_parser` closes over, each with the class
#: that decides whether it obstructs a relocation. This is the CLEANEST closure of the five large
#: functions (against `execute_item`'s 18 and `initialize_run`'s 34), which is why this function's
#: obstacle is "is it worth it" rather than "can it be done".
#:
#: ALREADY_SINGLE: module handles; both hosts import the same object, so a relocated core reaches
#: them unchanged.
ALREADY_SINGLE = ("argparse", "runner_shared", "runner_stop")

#: EQUAL_CONSTANTS: defined in both runners with EQUAL values. A relocation would need one home, but
#: no decision: neither host disagrees about the value.
EQUAL_CONSTANTS = ("ACTION_CHOICES", "DEFAULT_STALL_TIMEOUT")

#: STILL_DOUBLE_DEFINED: the only two names a relocation would actually have to resolve first. Both
#: are asserted STILL forked below, which is the inverse assertion this file exists to hold.
#:
#: `_add_output_mode_flags` IS ORPHANED BETWEEN TWO SIBLING PLANS (F-8), which is a fact about the
#: Set worth pinning rather than leaving in prose: child 04 (`tx6q0h`) lifts `_detect_driver_command`
#: and explicitly assigns `_add_output_mode_flags` to child 03, while child 03 (`i3d6ml`) was
#: re-scoped at its own review from 48 symbols to 9 (groups A and B) and group H, which holds
#: `_add_output_mode_flags`, was dropped. So no pending plan currently owns it.
STILL_DOUBLE_DEFINED = ("_add_output_mode_flags", "_detect_driver_command")

#: E-01(a) by the review's SOURCE-LITERAL method: option strings written as literals inside each
#: `build_parser`. Pinned because this is the number a source-level de-duplication changes, and
#: because it is the number this plan's review recorded; a reader meeting 17/7/10 in the plan and
#: 51/8/8 in the characterization suite must be able to see that both were measured.
LITERAL_PARTITION = {"shared": 17, "oc_only": 7, "agy_only": 10}

#: E-01(a) on the LIVE parser objects: what an operator actually meets.
#:
#: RE-MEASURED 2026-09-17 (shared 51 -> 52) by integpath-04 (`rl67b0`), which declared the `integrate`
#: subcommand on BOTH hosts through the ONE shared `runner_shared.add_integrate_parser`. The single new
#: entry is the positional `id6`; `--repo`, `-h` and `--help` were already shared, and `--run-id` is a
#: dest-form positional-free flag whose spelling both hosts already carried nowhere else. Because the
#: declaration is shared, the partition moved SYMMETRICALLY: neither `oc_only` nor `agy_only` changed,
#: which is exactly the property this table exists to police.
LIVE_PARTITION = {"shared": 52, "oc_only": 8, "agy_only": 8}

#: E-03: the residual de-duplication payoff, as a NUMBER rather than an impression. Identical
#: normalized code lines between the two `build_parser` bodies. THIS IS THE CEILING on what
#: relocating the function could remove.
#:
#: RE-MEASURED 2026-09-17 (23 -> 24) by integpath-04 (`rl67b0`). A RISE here is normally NOT progress,
#: so the reason is stated: the added line is IDENTICAL in both hosts precisely because the verb is
#: declared through ONE shared helper
#: (`runner_shared.add_integrate_parser(sub, command=_detect_driver_command())`), the same shape the
#: `stop` declaration beside it already uses. So the ceiling rose by one because one more line of this
#: function is now genuinely host-neutral, which is the direction this Set wants.
IDENTICAL_NORMALIZED_LINES = 24

#: E-03: `runner_shared.RUN_POLICY_FLAGS` rows, and the live option strings they account for.
POLICY_FLAG_ROWS = 12
POLICY_REGISTRATIONS_PER_HOST = 2
LIVE_STRINGS_FROM_POLICY_TABLE = 21


def module_body(name: str) -> list[ast.stmt]:
    return ast.parse((AW / f"{name}.py").read_text(encoding="utf-8")).body


def top_level_defs(name: str) -> dict[str, ast.stmt]:
    return {
        node.name: node
        for node in module_body(name)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    }


def module_level_names(name: str) -> set[str]:
    """Every module-level binding in `name`, however it is bound."""

    out: set[str] = set()
    for node in module_body(name):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            out.add(node.name)
        elif isinstance(node, ast.Assign):
            out.update(t.id for t in node.targets if isinstance(t, ast.Name))
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            out.add(node.target.id)
        elif isinstance(node, ast.Import):
            out.update(a.asname or a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            out.update(a.asname or a.name for a in node.names)
    return out


def target_node(host: str) -> ast.FunctionDef:
    node = top_level_defs(HOST_MODULE[host]).get("build_parser")
    assert isinstance(
        node, ast.FunctionDef
    ), f"{host} no longer defines build_parser at module level"
    return node


def free_module_level_names(host: str) -> set[str]:
    """`build_parser`'s closure: every free name it loads that the module binds.

    Re-derived here so the tables above cannot drift from the code that produced them. The property
    that must hold is NO FALSE NEGATIVE: a pinned name that stopped being reached must fail.
    """

    node = target_node(host)
    bound: set[str] = set()
    for child in ast.walk(node):
        if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Store):
            bound.add(child.id)
        elif isinstance(child, ast.arg):
            bound.add(child.arg)
        elif (
            isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
            and child is not node
        ):
            bound.add(child.name)
    loads = {
        n.id
        for n in ast.walk(node)
        if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)
    }
    module = module_level_names(HOST_MODULE[host])
    return {n for n in loads - bound if n in module and not hasattr(builtins, n)}


def literal_option_strings(host: str) -> set[str]:
    """Option-string LITERALS passed to `add_argument` inside this host's `build_parser`.

    The review's measurement method, reproduced exactly. It deliberately does NOT see
    `BooleanOptionalAction`'s auto-generated `--no-X`, nor anything a shared helper registers, which
    is precisely why it disagrees with the live count.
    """

    found: set[str] = set()
    for child in ast.walk(target_node(host)):
        if (
            isinstance(child, ast.Call)
            and isinstance(child.func, ast.Attribute)
            and child.func.attr == "add_argument"
        ):
            for arg in child.args:
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    found.add(arg.value)
    return found


def live_option_strings(host: str) -> set[str]:
    """Every option string (and positional dest) the host's built parser actually exposes."""

    got: set[str] = set()
    for action in HOSTS[host].build_parser()._actions:
        if isinstance(action, argparse._SubParsersAction):
            for sub in action.choices.values():
                for sub_action in sub._actions:
                    if isinstance(sub_action, argparse._SubParsersAction):
                        continue
                    got |= (
                        set(sub_action.option_strings)
                        if sub_action.option_strings
                        else {sub_action.dest}
                    )
            continue
        got |= set(action.option_strings) if action.option_strings else {action.dest}
    return got


def normalized_code_lines(host: str) -> list[str]:
    """`build_parser`'s body as normalized source lines, docstrings stripped.

    Normalizing through `ast.unparse` is what makes the comparison about CODE rather than about
    formatting: it collapses each call to one line and discards comments, so the residual figure
    below cannot be moved by a reflow.
    """

    tree = ast.parse(inspect.getsource(HOSTS[host].build_parser))
    for node in ast.walk(tree):
        body = getattr(node, "body", None)
        if (
            isinstance(body, list)
            and body
            and isinstance(body[0], ast.Expr)
            and isinstance(body[0].value, ast.Constant)
            and isinstance(body[0].value.value, str)
        ):
            node.body = body[1:]  # type: ignore[attr-defined]
    return [line for line in ast.unparse(tree).splitlines() if line.strip()]


class TheClosureClassificationIsPinned(unittest.TestCase):
    """E-01(b): all seven free names, each in the class that decides its effect on a relocation."""

    def test_the_closure_is_exactly_the_seven_names_measured(self):
        expected = (
            set(ALREADY_SINGLE) | set(EQUAL_CONSTANTS) | set(STILL_DOUBLE_DEFINED)
        )
        actual = free_module_level_names("oc")
        self.assertEqual(
            actual,
            expected,
            f"build_parser's closure changed: added={sorted(actual - expected)} "
            f"removed={sorted(expected - actual)}. A new free name is a new thing a relocation "
            f"must resolve; update the tables above in the SAME change and say which class it is in",
        )

    def test_the_three_classes_are_disjoint_so_the_table_cannot_contradict_itself(self):
        pairs = (
            ("ALREADY_SINGLE", ALREADY_SINGLE, "EQUAL_CONSTANTS", EQUAL_CONSTANTS),
            (
                "ALREADY_SINGLE",
                ALREADY_SINGLE,
                "STILL_DOUBLE_DEFINED",
                STILL_DOUBLE_DEFINED,
            ),
            (
                "EQUAL_CONSTANTS",
                EQUAL_CONSTANTS,
                "STILL_DOUBLE_DEFINED",
                STILL_DOUBLE_DEFINED,
            ),
        )
        for a_name, a, b_name, b in pairs:
            with self.subTest(pair=(a_name, b_name)):
                self.assertEqual(
                    set(a) & set(b), set(), f"{a_name} and {b_name} overlap"
                )

    def test_the_already_single_names_really_are_one_object_on_both_hosts(self):
        for name in ALREADY_SINGLE:
            with self.subTest(name=name):
                self.assertIs(
                    getattr(oc_runipd, name),
                    getattr(agy_runipd, name),
                    f"{name} is no longer the same object from both hosts, so it has stopped being "
                    f"a free ride for a relocation",
                )

    def test_the_equal_constants_are_defined_twice_but_agree(self):
        """Two homes, no disagreement: a relocation needs one home and no decision."""

        for name in EQUAL_CONSTANTS:
            with self.subTest(name=name):
                for module in HOST_MODULE.values():
                    self.assertIn(
                        name,
                        module_level_names(module),
                        f"{name} is no longer bound at module level in {module}",
                    )
                self.assertEqual(
                    getattr(oc_runipd, name),
                    getattr(agy_runipd, name),
                    f"{name} now DIFFERS between the hosts; it has moved from EQUAL_CONSTANTS to a "
                    f"genuine behavior conflict and needs a decision, not a lift",
                )

    def test_the_measured_values_of_the_equal_constants_have_not_drifted(self):
        """Pinned by VALUE too, so "equal" cannot be satisfied by both hosts changing together."""

        self.assertEqual(oc_runipd.ACTION_CHOICES, ("review", "plan", "execute"))
        self.assertEqual(oc_runipd.DEFAULT_STALL_TIMEOUT, 600.0)


class TheFlagPartitionIsPinnedByBothMeasurementMethods(unittest.TestCase):
    """E-01(a): 17/7/10 by source literal, 51/8/8 live. Both true, and both pinned.

    PINNING BOTH IS THE POINT. A future reader meeting two different partitions in this plan's
    records needs the discrepancy to be a recorded measurement rather than an apparent error, and a
    future de-duplication needs to know which number its change is expected to move.
    """

    def test_the_source_literal_partition_is_the_reviews_seventeen_seven_ten(self):
        oc_lit, agy_lit = literal_option_strings("oc"), literal_option_strings("agy")
        actual = {
            "shared": len(oc_lit & agy_lit),
            "oc_only": len(oc_lit - agy_lit),
            "agy_only": len(agy_lit - oc_lit),
        }
        self.assertEqual(
            actual,
            LITERAL_PARTITION,
            "the SOURCE-LITERAL flag partition moved. This is the number a source-level "
            "de-duplication changes; if a relocation caused it, that is expected and this table "
            "should be updated in the same change",
        )

    def test_the_live_partition_is_fifty_one_eight_eight(self):
        oc_live, agy_live = live_option_strings("oc"), live_option_strings("agy")
        actual = {
            "shared": len(oc_live & agy_live),
            "oc_only": len(oc_live - agy_live),
            "agy_only": len(agy_live - oc_live),
        }
        self.assertEqual(
            actual,
            LIVE_PARTITION,
            "the LIVE flag partition moved, which means an operator-visible command line changed. "
            "See TheVerificationDestAsymmetryIsPinnedPerHost in this file for which flag",
        )

    def test_the_two_methods_genuinely_disagree_so_neither_pin_is_redundant(self):
        """The discrepancy itself, asserted, so nobody "fixes" one number to match the other.

        If these two ever agreed, one of the two measurements would have stopped measuring what it
        was written to measure.
        """

        self.assertLess(
            LITERAL_PARTITION["shared"],
            LIVE_PARTITION["shared"],
            "the source-literal method must under-count the live surface; that gap IS the "
            "auto-generated and helper-registered flags",
        )
        oc_lit, oc_live = literal_option_strings("oc"), live_option_strings("oc")
        self.assertTrue(
            oc_lit <= oc_live,
            f"a literal that is not live: {sorted(oc_lit - oc_live)}. Every literal written in "
            f"build_parser must reach the built parser",
        )
        self.assertIn(
            "--no-allow-mixed",
            oc_live - oc_lit,
            "an auto-generated --no-X must be live but not literal; that is the mechanism the two "
            "methods differ over",
        )


VERIFICATION_FLAGS = (
    "--validate",
    "--no-validate",
    "--verify",
    "--no-verify",
    "--audit",
    "--no-audit",
)

#: E-01(a) measured at execution HEAD `4a1bb873`. Per host, per subparser, the EXACT set of option
#: strings that subparser registers. A table rather than prose so an addition or a removal fails
#: with the flag named, and so the two hosts' surfaces can be compared without either suite
#: guessing at the other's.
#:
#: `-h`/`--help` is included rather than filtered: argparse adds it, and a shared core that
#: suppressed it on one host would be an operator-visible change this plan must catch.
EXPECTED_OPTION_STRINGS: dict[str, dict[str, frozenset[str]]] = {
    "oc": {
        # integpath-04 (`rl67b0`): the `integrate` verb, declared through the ONE shared
        # `runner_shared.add_integrate_parser`, so BOTH hosts carry the identical row.
        "integrate": frozenset({"--help", "--repo", "--run-id", "-h", "id6"}),
        "report": frozenset({"--help", "--repo", "-h", "run_id"}),
        "resume": frozenset(
            {
                "--allow-dirty-base",
                "--allow-drafts",
                "--allow-mixed",
                "--allow-unverifiable",
                "--audit",
                "--follow-generated",
                "--full-auto",
                "--help",
                "--integration-retry-limit",
                "--max-items-per-session",
                "--no-allow-dirty-base",
                "--no-allow-drafts",
                "--no-allow-mixed",
                "--no-allow-unverifiable",
                "--no-audit",
                "--no-follow-generated",
                "--no-full-auto",
                "--no-unattended",
                "--no-unverifiable-ok",
                "--no-validate",
                "--no-verify",
                "--no-with-dependencies",
                "--on-integration-blocked",
                "--quiet",
                "--raw",
                "--repo",
                "--retry-budget",
                "--retry-incomplete",
                "--session",
                "--stall-timeout",
                "--unattended",
                "--unverifiable-ok",
                "--validate",
                "--variant",
                "--verbose",
                "--verify",
                "--verify-with",
                "--with-dependencies",
                "-h",
                "-v",
                "run_id",
            }
        ),
        "start": frozenset(
            {
                "--action",
                "--agent",
                "--allow-dirty-base",
                "--allow-drafts",
                "--allow-mixed",
                "--allow-unverifiable",
                "--audit",
                "--auto",
                "--follow-generated",
                "--full-auto",
                "--help",
                "--integration-retry-limit",
                "--manifest",
                "--max-items-per-session",
                "--model",
                "--no-allow-dirty-base",
                "--no-allow-drafts",
                "--no-allow-mixed",
                "--no-allow-unverifiable",
                "--no-audit",
                "--no-auto",
                "--no-follow-generated",
                "--no-full-auto",
                "--no-isolate-worktree",
                "--no-self-finalize",
                "--no-unattended",
                "--no-unverifiable-ok",
                "--no-validate",
                "--no-verify",
                "--no-with-dependencies",
                "--on-integration-blocked",
                "--opencode",
                "--prepare-only",
                "--quiet",
                "--raw",
                "--repo",
                "--retry-budget",
                "--run-id",
                "--runbook",
                "--session",
                "--stall-timeout",
                "--unattended",
                "--unverifiable-ok",
                "--validate",
                "--variant",
                "--verbose",
                "--verify",
                "--verify-with",
                "--with-dependencies",
                "-h",
                "-v",
                "selectors",
            }
        ),
        "status": frozenset({"--help", "--json", "--repo", "-h", "run_id"}),
        "stop": frozenset(
            {
                "--after-call",
                "--after-set",
                "--help",
                "--now",
                "--now-force",
                "--repo",
                "-h",
                "run_id",
            }
        ),
    },
    "agy": {
        # integpath-04 (`rl67b0`): the `integrate` verb, declared through the ONE shared
        # `runner_shared.add_integrate_parser`, so BOTH hosts carry the identical row.
        "integrate": frozenset({"--help", "--repo", "--run-id", "-h", "id6"}),
        "report": frozenset({"--help", "--repo", "-h", "run_id"}),
        "resume": frozenset(
            {
                "--agy",
                "--agy-executable",
                "--allow-dirty-base",
                "--allow-drafts",
                "--allow-mixed",
                "--allow-unverifiable",
                "--follow-generated",
                "--full-auto",
                "--help",
                "--integration-retry-limit",
                "--max-items-per-session",
                "--no-allow-dirty-base",
                "--no-allow-drafts",
                "--no-allow-mixed",
                "--no-allow-unverifiable",
                "--no-follow-generated",
                "--no-full-auto",
                "--no-unattended",
                "--no-unverifiable-ok",
                "--no-with-dependencies",
                "--on-integration-blocked",
                "--quiet",
                "--raw",
                "--repo",
                "--retry-budget",
                "--retry-incomplete",
                "--session",
                "--stall-timeout",
                "--unattended",
                "--unverifiable-ok",
                "--verbose",
                "--with-dependencies",
                "-h",
                "-v",
                "run_id",
            }
        ),
        "start": frozenset(
            {
                "--action",
                "--agy",
                "--agy-executable",
                "--allow-dirty-base",
                "--allow-drafts",
                "--allow-mixed",
                "--allow-unverifiable",
                "--dangerous",
                "--dangerously-skip-permissions",
                "--effort",
                "--follow-generated",
                "--full-auto",
                "--help",
                "--integration-retry-limit",
                "--manifest",
                "--max-items-per-session",
                "--model",
                "--new-session",
                "--no-allow-dirty-base",
                "--no-allow-drafts",
                "--no-allow-mixed",
                "--no-allow-unverifiable",
                "--no-audit",
                "--no-dangerously-skip-permissions",
                "--no-follow-generated",
                "--no-full-auto",
                "--no-isolate-worktree",
                "--no-self-finalize",
                "--no-unattended",
                "--no-unverifiable-ok",
                "--no-validate",
                "--no-verify",
                "--no-with-dependencies",
                "--on-integration-blocked",
                "--prepare-only",
                "--quiet",
                "--raw",
                "--repo",
                "--retry-budget",
                "--run-id",
                "--runbook",
                "--session",
                "--stall-timeout",
                "--timeout",
                "--unattended",
                "--unverifiable-ok",
                "--validate",
                "--verbose",
                "--with-dependencies",
                "-h",
                "-v",
                "selectors",
            }
        ),
        "status": frozenset({"--help", "--json", "--repo", "-h", "run_id"}),
        "stop": frozenset(
            {
                "--after-call",
                "--after-set",
                "--help",
                "--now",
                "--now-force",
                "--repo",
                "-h",
                "run_id",
            }
        ),
    },
}


def subparsers(host: str) -> dict[str, argparse.ArgumentParser]:
    """Every subparser the host's `build_parser` registers, by name.

    Reached through the parser OBJECT (the `_SubParsersAction`'s `choices`), so this survives the
    function being relocated to `runner_shared`.
    """

    parser = HOSTS[host].build_parser()
    found: dict[str, argparse.ArgumentParser] = {}
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            found.update(action.choices)
    return found


def option_strings(parser: argparse.ArgumentParser) -> set[str]:
    """Every option string, plus every POSITIONAL's dest, registered on this parser.

    Positionals are included by dest because `selectors` and `run_id` are as much a part of the
    operator-visible surface as any flag, and a shared core dropping one would otherwise pass.
    """

    got: set[str] = set()
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            continue
        if action.option_strings:
            got.update(action.option_strings)
        else:
            got.add(action.dest)
    return got


def dest_of(parser: argparse.ArgumentParser, flag: str) -> str | None:
    """The `dest` `flag` resolves to on `parser`, or `None` when the flag is not registered.

    This is the function that makes F-7 testable: the collision hazard is a property of HOW the
    parser was built, so it is only decidable here and not on a parsed namespace.
    """

    for action in parser._actions:
        if flag in (action.option_strings or []):
            return action.dest
    return None


class EachHostRegistersExactlyItsOwnFlagSet(unittest.TestCase):
    """The per-host flag contract, asserted from a table so a drift names the flag.

    THIS IS THE CLASS THE SPLIT NEEDS. A shared `build_parser` core is a refactor whose whole risk
    is that one host's command line quietly changes; `test_run_flag_surface.py` cannot see that for
    any flag outside spec 2.1's twelve policy rows, which is most of them (measured: 51 shared
    option strings live on these parsers against 12 policy rows).
    """

    def test_the_two_hosts_register_the_same_six_subparsers(self):
        # SIX since 2026-09-17: integpath-04 (`rl67b0`) added `integrate`, declared on BOTH hosts through
        # the ONE shared `runner_shared.add_integrate_parser`, exactly as `stop` is. What this test is
        # actually about is that the two hosts register the SAME set, and they still do.
        for host in HOSTS:
            with self.subTest(host=host):
                self.assertEqual(
                    sorted(subparsers(host)),
                    ["integrate", "report", "resume", "start", "status", "stop"],
                    f"{host} no longer registers exactly the six expected subparsers",
                )

    def test_every_subparser_registers_exactly_the_measured_option_strings(self):
        for host, expected_by_sub in EXPECTED_OPTION_STRINGS.items():
            live = subparsers(host)
            for sub_name, expected in expected_by_sub.items():
                with self.subTest(host=host, subparser=sub_name):
                    actual = option_strings(live[sub_name])
                    added = sorted(actual - expected)
                    removed = sorted(expected - actual)
                    self.assertEqual(
                        (added, removed),
                        ([], []),
                        f"{host} `{sub_name}` flag surface CHANGED: added={added} "
                        f"removed={removed}. If this change is intended, update "
                        f"EXPECTED_OPTION_STRINGS in the SAME change and say why; if it is not, a "
                        f"refactor has altered an operator-visible command line",
                    )

    def test_the_table_is_not_stale_against_the_live_subparser_names(self):
        """The table cannot silently stop covering a subparser that exists.

        Without this, adding a sixth subparser would leave it entirely unpinned while every
        assertion above still passed.
        """

        for host in HOSTS:
            with self.subTest(host=host):
                self.assertEqual(
                    sorted(EXPECTED_OPTION_STRINGS[host]),
                    sorted(subparsers(host)),
                    f"the {host} table does not cover every subparser {host} registers",
                )

    def test_the_host_only_partition_is_what_was_measured(self):
        """The 8 oc-only / 8 agy-only split of the LIVE surface, asserted with members.

        NOTE THE NUMBERS, because they differ from this plan's review and the difference is
        explained rather than papered over. The review recorded 17 shared / 7 oc-only / 10 agy-only
        by counting option-string LITERALS in each `build_parser` source; that method cannot see a
        `--no-X` that `BooleanOptionalAction` auto-generates, nor anything a shared helper
        registers. Counted on the LIVE parsers, which is what an operator actually meets, the
        partition is 52 shared / 8 oc-only / 8 agy-only.

        RE-MEASURED 2026-09-17 (shared 51 -> 52) by integpath-04 (`rl67b0`): the `integrate` verb's
        positional `id6` is the one new shared entry, and because the verb is declared through ONE
        shared helper the partition moved SYMMETRICALLY. Neither host-only set changed, which is the
        property this test exists to police.
        """

        oc_all: set[str] = set()
        agy_all: set[str] = set()
        for host, bucket in (("oc", oc_all), ("agy", agy_all)):
            for sub in subparsers(host).values():
                bucket |= option_strings(sub)

        self.assertEqual(
            sorted(oc_all - agy_all),
            [
                "--agent",
                "--audit",
                "--auto",
                "--no-auto",
                "--opencode",
                "--variant",
                "--verify",
                "--verify-with",
            ],
            "the oc-only flag set changed",
        )
        self.assertEqual(
            sorted(agy_all - oc_all),
            [
                "--agy",
                "--agy-executable",
                "--dangerous",
                "--dangerously-skip-permissions",
                "--effort",
                "--new-session",
                "--no-dangerously-skip-permissions",
                "--timeout",
            ],
            "the agy-only flag set changed",
        )
        self.assertEqual(
            len(oc_all & agy_all),
            52,
            "the number of SHARED option strings changed; a flag became host-specific or stopped "
            "being so",
        )


class TheVerificationDestAsymmetryIsPinnedPerHost(unittest.TestCase):
    """F-7 made executable: `--no-verify` means different things on the two hosts, BY DESIGN.

    THIS IS THE ASSERTION THAT REFUSES THE OC-PREFERRED RULING for this symbol. The Set's rule is
    "resolve a difference to the oc version unless it is a real capability". Here the difference IS
    the capability: adopting oc's `--verify`/`--audit` aliases on agy makes `BooleanOptionalAction`
    auto-generate `--no-verify`/`--no-audit` and steal agy's shipped spellings, which is precisely
    what `agy_runipd.assert_verification_flags_are_distinct` exists to catch.

    WHEN THE SPLIT HAPPENS this class must be RE-BASED and not deleted: whatever mechanism hands
    the shared core each host's verification-flag policy must still produce exactly these dests, and
    this class is how that is proven rather than assumed.
    """

    def test_oc_collapses_all_six_spellings_onto_one_dest(self):
        for sub_name in ("start", "resume"):
            with self.subTest(subparser=sub_name):
                parser = subparsers("oc")[sub_name]
                actual = {flag: dest_of(parser, flag) for flag in VERIFICATION_FLAGS}
                self.assertEqual(
                    actual,
                    {flag: "validate" for flag in VERIFICATION_FLAGS},
                    "oc's six verification spellings must ALL resolve to dest `validate`; on this "
                    "host they are aliases of one tri-state",
                )

    def test_agy_splits_the_spellings_across_two_dests_and_omits_two(self):
        parser = subparsers("agy")["start"]
        self.assertEqual(
            {flag: dest_of(parser, flag) for flag in VERIFICATION_FLAGS},
            {
                "--validate": "validate",
                "--no-validate": "validate",
                "--verify": None,
                "--no-verify": "no_verify",
                "--audit": None,
                "--no-audit": "no_verify",
            },
            "agy's verification surface must stay DISTINCT from oc's: `--verify`/`--audit` do not "
            "exist here, and `--no-verify`/`--no-audit` carry their own dest `no_verify`. If this "
            "failed after a de-duplication, oc's alias list has been registered on agy and agy's "
            "shipped `--no-verify` no longer means what its documentation says",
        )

    def test_agy_registers_no_verification_flags_on_resume_at_all(self):
        """The measured fact, pinned so a split cannot ADD flags to agy's resume by accident.

        A shared core that registered oc's `resume` verification block on both hosts would give
        agy six new flags. That is an operator-visible addition, and spec-surface tests would not
        catch it for the four spellings outside spec 2.1's policy rows.
        """

        parser = subparsers("agy")["resume"]
        self.assertEqual(
            {flag: dest_of(parser, flag) for flag in VERIFICATION_FLAGS},
            {flag: None for flag in VERIFICATION_FLAGS},
            "agy's `resume` registers NONE of the six verification spellings; a split must not "
            "give it any",
        )

    def test_agys_build_time_collision_guard_is_still_called_and_still_passes(self):
        """The guard must be INVOKED by `build_parser`, not merely present in the module.

        Building the parser is the proof: `assert_verification_flags_are_distinct` raises
        `DriverError` on a collision, so a successful build is a passing guard. Importing the
        module would establish nothing.
        """

        parser = (
            agy_runipd.build_parser()
        )  # raises DriverError if the spellings collided
        self.assertIsNotNone(parser)
        # And the guard still refuses the collision it was installed for, so it is not vacuous.
        stolen = argparse.ArgumentParser()
        stolen.add_argument(
            "--validate",
            "--verify",
            "--audit",
            dest="validate",
            action=argparse.BooleanOptionalAction,
            default=None,
        )
        with self.assertRaises(agy_runipd.DriverError):
            agy_runipd.assert_verification_flags_are_distinct(stolen)

    def test_oc_has_no_such_guard_and_does_not_need_one(self):
        """The asymmetry's other half, asserted so it reads as a decision rather than an omission.

        oc registers ONE action for all six spellings, so there is nothing to collide. A future
        agent tempted to "add the missing guard to oc for symmetry" should read this first.
        """

        self.assertFalse(
            hasattr(oc_runipd, "assert_verification_flags_are_distinct"),
            "oc has acquired a verification-collision guard; if that is deliberate, this "
            "assertion should be replaced with one that pins what the new guard asserts",
        )
        parser = subparsers("oc")["start"]
        aliases = [
            action.option_strings
            for action in parser._actions
            if action.dest == "validate" and action.option_strings
        ]
        self.assertEqual(
            len(aliases),
            1,
            "oc's six verification spellings must remain ONE action; splitting them into several "
            "is the state agy's guard refuses",
        )


class TheBranchesASplitWouldMoveAreCharacterized(unittest.TestCase):
    """Behavioral characterization of what `build_parser` actually PRODUCES, both hosts.

    THE PARENT SET'S CONSTRAINT is that a child may not change what a runner does, and forbids
    reconciling a symbol the characterization baseline has not pinned. For a parser, "what it does"
    is: which subparser a command line selects, what defaults it freezes, and how a flag parses. All
    of that is asserted here on the parsed `Namespace`, so it survives relocation.

    AGY IS COVERED DELIBERATELY. The parent measured the two hosts' suites as asymmetric (95 oc
    tests against 21 agy at the time), so every assertion below runs against BOTH hosts unless the
    property is genuinely host-specific, and the agy-only defaults are pinned explicitly.
    """

    def test_a_bare_start_parses_and_freezes_the_measured_defaults_on_both_hosts(self):
        expected_shared = {
            "output_mode": "clean",
            "verbosity": 0,
            "prepare_only": False,
            "stall_timeout": 600.0,
            "self_finalize": True,
            "isolate_worktree": True,
        }
        for host in HOSTS:
            with self.subTest(host=host):
                args = HOSTS[host].build_parser().parse_args(["start", "s16omw"])
                self.assertEqual(args.command, "start")
                self.assertEqual(args.selectors, ["s16omw"])
                for key, value in expected_shared.items():
                    self.assertEqual(
                        getattr(args, key),
                        value,
                        f"{host} start default for {key} changed",
                    )

    def test_the_output_mode_flags_are_mutually_exclusive_on_both_hosts(self):
        """`--quiet` and `--raw` choose WHICH renderer runs, so both at once is refused.

        This is a property of `_add_output_mode_flags`, which is one of only two symbols in this
        function's closure still defined twice, and which is currently owned by no sibling plan
        (F-8). Pinning it behaviorally on both hosts means whichever plan eventually shares it has
        a test that already spans both.
        """

        for host in HOSTS:
            with self.subTest(host=host):
                parser = HOSTS[host].build_parser()
                self.assertEqual(
                    parser.parse_args(["start", "x", "--quiet"]).output_mode, "quiet"
                )
                self.assertEqual(
                    parser.parse_args(["start", "x", "--raw"]).output_mode, "raw"
                )
                with self.assertRaises(SystemExit):
                    parser.parse_args(["start", "x", "--quiet", "--raw"])

    def test_resume_leaves_verbosity_absent_so_a_frozen_tier_survives_on_both_hosts(
        self,
    ):
        """`verbosity_default` is 0 on `start` and None on `resume`, on BOTH hosts.

        The distinction is load-bearing: an omitted `-v` on resume must not silently reset a frozen
        tier to 0. A shared core that passed one default for both subcommands would break it, and
        no spec-surface test would notice.
        """

        for host in HOSTS:
            with self.subTest(host=host):
                parser = HOSTS[host].build_parser()
                self.assertIsNone(parser.parse_args(["resume", "run-x"]).verbosity)
                self.assertEqual(
                    parser.parse_args(["resume", "run-x", "-vv"]).verbosity, 2
                )

    def test_the_action_choices_are_constrained_identically_on_both_hosts(self):
        for host in HOSTS:
            with self.subTest(host=host):
                parser = HOSTS[host].build_parser()
                self.assertEqual(
                    parser.parse_args(["start", "x", "--action", "review"]).action,
                    "review",
                )
                with self.assertRaises(SystemExit):
                    parser.parse_args(["start", "x", "--action", "nonsense"])

    def test_agy_only_start_defaults_are_what_was_measured(self):
        """agy's own flags, pinned because a shared core must not drop or re-default them."""

        args = agy_runipd.build_parser().parse_args(["start", "x"])
        self.assertIsNone(args.validate)
        self.assertFalse(args.no_verify)
        self.assertIsNone(
            args.effort,
            "agy's --effort has no default; the host decides downstream, and a shared core "
            "inventing one here would change what a bare `start` requests",
        )
        self.assertFalse(args.new_session)
        self.assertEqual(
            args.timeout,
            agy_runipd.DEFAULT_TIMEOUT,
            "agy's --timeout default must remain the module constant, not a literal a shared "
            "core supplies",
        )
        self.assertEqual(
            args.timeout, "240m", "the measured value of DEFAULT_TIMEOUT changed"
        )
        self.assertIs(
            args.dangerously_skip_permissions,
            True,
            "agy's --dangerously-skip-permissions DEFAULTS TO TRUE, which is the opposite of what "
            "the flag name suggests and is exactly why it is pinned: a shared core that supplied "
            "the safer-looking default would silently change this host's launch posture",
        )

    def test_oc_only_start_defaults_are_what_was_measured(self):
        """oc's own flags, the mirror of the agy assertion above."""

        args = oc_runipd.build_parser().parse_args(["start", "x"])
        self.assertIsNone(args.validate)
        self.assertIsNone(args.variant)
        self.assertIsNone(args.agent)
        self.assertFalse(hasattr(args, "no_verify"))
        self.assertFalse(
            hasattr(args, "effort"),
            "oc has acquired agy's --effort; that is an operator-visible addition",
        )

    def test_the_verification_tristate_reads_each_hosts_flags_as_measured(self):
        """The dest asymmetry's CONSEQUENCE, not just its shape.

        Proving the parsed namespace feeds each host's own tri-state resolver correctly is what
        makes the dest table above matter. On agy, `--no-verify` and `--validate` together are a
        CONTRADICTION the host refuses rather than resolving by precedence.
        """

        agy_parser = agy_runipd.build_parser()
        self.assertIs(
            agy_runipd.verification_flag_tristate(
                agy_parser.parse_args(["start", "x"])
            ),
            None,
        )
        self.assertIs(
            agy_runipd.verification_flag_tristate(
                agy_parser.parse_args(["start", "x", "--no-verify"])
            ),
            False,
        )
        self.assertIs(
            agy_runipd.verification_flag_tristate(
                agy_parser.parse_args(["start", "x", "--validate"])
            ),
            True,
        )
        with self.assertRaises(Exception):
            agy_runipd.verification_flag_tristate(
                agy_parser.parse_args(["start", "x", "--no-verify", "--validate"])
            )

        oc_parser = oc_runipd.build_parser()
        self.assertIs(oc_parser.parse_args(["start", "x", "--verify"]).validate, True)
        self.assertIs(
            oc_parser.parse_args(["start", "x", "--no-verify"]).validate, False
        )
        self.assertIs(oc_parser.parse_args(["start", "x", "--audit"]).validate, True)

    def test_the_run_policy_flags_parse_identically_on_both_hosts(self):
        """The already-shared half (F-3), asserted to BE shared behaviorally.

        These twelve rows are registered from `runner_shared.register_run_policy_flags`, so they
        should parse the same on both hosts. Asserting it means a future host-side override shows
        up here rather than in a production incident.
        """

        for host in HOSTS:
            with self.subTest(host=host):
                parser = HOSTS[host].build_parser()
                args = parser.parse_args(
                    ["start", "x", "--allow-mixed", "--retry-budget", "5"]
                )
                self.assertTrue(args.allow_mixed)
                self.assertEqual(args.retry_budget, 5)
                self.assertFalse(
                    parser.parse_args(["start", "x", "--no-allow-mixed"]).allow_mixed
                )
                with self.assertRaises(SystemExit):
                    parser.parse_args(
                        ["start", "x", "--on-integration-blocked", "nonsense"]
                    )

    def test_status_and_report_accept_a_run_id_and_repo_on_both_hosts(self):
        for host in HOSTS:
            with self.subTest(host=host):
                parser = HOSTS[host].build_parser()
                args = parser.parse_args(["status", "run-x", "--json"])
                self.assertEqual(
                    (args.command, args.run_id, args.json), ("status", "run-x", True)
                )
                self.assertEqual(parser.parse_args(["report", "run-y"]).run_id, "run-y")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
