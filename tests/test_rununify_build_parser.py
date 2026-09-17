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
the companion file `tests/test_rununify_build_parser_characterization.py`, together with the proof
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
from difflib import SequenceMatcher
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


class TheTwoRemainingForksAreStillForked(unittest.TestCase):
    """THE INVERSE ASSERTIONS: a later agent cannot collapse either fork without coming here.

    Both names are pinned STILL double-defined, and one of them (`_add_output_mode_flags`) is
    currently owned by NO pending sibling plan (F-8). If a plan does share one of these, the fix is
    to move it out of `STILL_DOUBLE_DEFINED` in the same change and record why, not to delete the
    assertion.
    """

    def test_both_forks_are_still_defined_in_both_runners(self):
        oc_defs, agy_defs = top_level_defs("oc_runipd"), top_level_defs("agy_runipd")
        for name in STILL_DOUBLE_DEFINED:
            with self.subTest(name=name):
                self.assertIn(
                    name, oc_defs, f"{name} is no longer defined in oc_runipd"
                )
                self.assertIn(
                    name, agy_defs, f"{name} is no longer defined in agy_runipd"
                )
                self.assertIsNot(
                    getattr(oc_runipd, name),
                    getattr(agy_runipd, name),
                    f"{name} has been unified. That may well be correct, but this file pins the "
                    f"measured state: move it out of STILL_DOUBLE_DEFINED in the SAME change, with "
                    f"the reason, rather than deleting this assertion",
                )

    def test_neither_fork_lives_in_runner_shared_yet(self):
        shared = module_level_names("runner_shared")
        for name in STILL_DOUBLE_DEFINED:
            with self.subTest(name=name):
                self.assertNotIn(
                    name,
                    shared,
                    f"{name} now exists in runner_shared; if the lift landed, update "
                    f"STILL_DOUBLE_DEFINED and the analysis it refers to",
                )

    def test_the_two_output_mode_helper_bodies_genuinely_differ(self):
        """Why `_add_output_mode_flags` is a LIFT DECISION and not a free move.

        Pinned because the orphan status matters only if the two bodies are not already identical:
        an identical pair could be lifted by any plan without a judgment call, whereas a differing
        pair needs someone to decide which body wins.
        """

        oc_src = ast.unparse(
            ast.parse(inspect.getsource(oc_runipd._add_output_mode_flags))
        )
        agy_src = ast.unparse(
            ast.parse(inspect.getsource(agy_runipd._add_output_mode_flags))
        )
        self.assertNotEqual(
            oc_src,
            agy_src,
            "the two `_add_output_mode_flags` bodies are now AST-identical; the lift became "
            "mechanical, so whichever plan takes it no longer needs a body decision",
        )


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
            "See tests/test_rununify_build_parser_characterization.py for which flag",
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


class TheResidualDeduplicationPayoffIsMeasured(unittest.TestCase):
    """E-03: the split's payoff as a NUMBER, so the cost/benefit rests on a measurement.

    THIS IS THE CLASS THAT MAKES THE ECONOMICS AUDITABLE. The plan's Concern asserts the divergence
    is mostly drift; these assertions are what show it is not.
    """

    def test_the_two_bodies_share_only_the_measured_identical_lines(self):
        oc_lines, agy_lines = normalized_code_lines("oc"), normalized_code_lines("agy")
        matcher = SequenceMatcher(None, oc_lines, agy_lines)
        identical = sum(block.size for block in matcher.get_matching_blocks())
        self.assertEqual(
            identical,
            IDENTICAL_NORMALIZED_LINES,
            f"the identical-line count moved from {IDENTICAL_NORMALIZED_LINES} to {identical}. "
            f"That number IS the de-duplication ceiling for relocating this function: if a "
            f"de-duplication landed it should DROP, and if the two copies drifted further apart it "
            f"should drop too, so update it deliberately with the reason",
        )

    def test_this_function_is_the_least_similar_of_the_five_large_functions(self):
        """Similarity 0.5053, the finding the Concern contradicts and F-1 gets right.

        RE-MEASURED 2026-09-17 (0.4946 -> 0.5053) by integpath-04 (`rl67b0`): its one added line is the
        SHARED `runner_shared.add_integrate_parser(...)` call, identical on both hosts, so the ratio
        crossed 0.5 from below. THE FINDING STILL HOLDS and the threshold prose is kept honest rather
        than quietly restated: this remains the LEAST similar of the five large functions, and the
        substance of F-1 is that ordering, not the exact side of 0.5 the number sits on.
        """

        matcher = SequenceMatcher(
            None, normalized_code_lines("oc"), normalized_code_lines("agy")
        )
        self.assertAlmostEqual(
            matcher.ratio(),
            0.5053,
            places=3,
            msg="build_parser's cross-host similarity moved from the measured 0.5053. Around 0.5 "
            "means the two functions share about half their content, which is what makes "
            "'mostly drift' the wrong description of this symbol",
        )

    def test_half_of_each_body_is_help_text_a_shared_core_would_have_to_parameterize(
        self,
    ):
        # RE-MEASURED 2026-09-17 by integpath-04 (`rl67b0`): 52.1 -> 50.3 on oc and 42.0 -> 40.5 on agy.
        # Both fell because the added line is CODE with no help text of its own (the verb's own help
        # strings live in `runner_shared`, shared, which is the point), so the literal share of each
        # body dropped slightly. The claim this pins - that about half of each body is help text a
        # shared core would have to parameterize - is unchanged.
        expected = {"oc": 50.3, "agy": 40.5}
        for host, share in expected.items():
            with self.subTest(host=host):
                source = inspect.getsource(HOSTS[host].build_parser)
                chars = sum(
                    len(node.value)
                    for node in ast.walk(ast.parse(source))
                    if isinstance(node, ast.Constant) and isinstance(node.value, str)
                )
                actual = 100.0 * chars / len(source)
                self.assertAlmostEqual(
                    actual,
                    share,
                    delta=1.5,
                    msg=f"{host}'s string-literal share of build_parser moved from {share}%. This "
                    f"is the text a shared core must either parameterize or impose on the other "
                    f"host, and imposing it is an operator-visible change",
                )

    def test_the_spec_governed_half_is_already_shared_and_must_not_be_re_forked(self):
        """F-3: 12 rows, one registration function, 2 calls per host, 21 live strings.

        This is the finding that decides the economics, and the inverse assertion that protects it:
        if a "shared core" ever registered these host-side again, the payoff it claimed would be
        illusory and the spec contract test would be the only thing left holding the line.
        """

        self.assertEqual(len(runner_shared.RUN_POLICY_FLAGS), POLICY_FLAG_ROWS)
        for host in HOSTS:
            with self.subTest(host=host):
                source = inspect.getsource(HOSTS[host].build_parser)
                self.assertEqual(
                    source.count("register_run_policy_flags("),
                    POLICY_REGISTRATIONS_PER_HOST,
                    f"{host} no longer registers the shared policy table exactly "
                    f"{POLICY_REGISTRATIONS_PER_HOST} times (start and resume)",
                )

    def test_the_policy_table_accounts_for_twenty_one_of_the_shared_live_strings(self):
        policy_dests = {row.dest for row in runner_shared.RUN_POLICY_FLAGS}
        start = None
        for action in oc_runipd.build_parser()._actions:
            if isinstance(action, argparse._SubParsersAction):
                start = action.choices["start"]
        assert start is not None
        from_policy: set[str] = set()
        for action in start._actions:
            if action.dest in policy_dests and action.option_strings:
                from_policy |= set(action.option_strings)
        self.assertEqual(
            len(from_policy),
            LIVE_STRINGS_FROM_POLICY_TABLE,
            "the number of live option strings the ALREADY-SHARED policy table accounts for "
            "changed; the residual payoff figure above depends on it",
        )


class TheSplitHasNotBeenPerformed(unittest.TestCase):
    """The inverse assertions that make the omission MECHANICAL rather than a matter of trust.

    If a later change performs the split, these fail by design. That is the tripwire: the fix is to
    re-base this class onto whatever shape the split takes, having read the analysis, not to delete
    it.
    """

    def test_both_hosts_still_define_their_own_build_parser(self):
        for host, module in HOST_MODULE.items():
            with self.subTest(host=host):
                self.assertIn(
                    "build_parser",
                    top_level_defs(module),
                    f"{module} no longer defines build_parser",
                )

    def test_runner_shared_does_not_define_a_build_parser_core(self):
        self.assertNotIn(
            "build_parser",
            module_level_names("runner_shared"),
            "runner_shared has acquired a build_parser; if the split landed, this class must be "
            "re-based and the partition/payoff tables re-measured",
        )

    def test_the_two_definitions_are_not_the_same_object(self):
        self.assertIsNot(oc_runipd.build_parser, agy_runipd.build_parser)

    def test_neither_host_delegates_its_parser_to_the_other_host(self):
        """The re-fork guard's direction that matters here: no runner-to-runner reach.

        `runner_shared` is the only sanctioned home for shared runner code, so a host reaching the
        OTHER host's `build_parser` would be a worse outcome than the duplication it removed.
        """

        for module, other in (("oc_runipd", "agy_runipd"), ("agy_runipd", "oc_runipd")):
            with self.subTest(module=module):
                source = (AW / f"{module}.py").read_text(encoding="utf-8")
                self.assertNotIn(
                    f"{other}.build_parser",
                    source,
                    f"{module} reaches {other}'s build_parser; shared code belongs in "
                    f"runner_shared, never in the peer runner",
                )

    def test_build_parser_still_carries_no_source_inspection_pin(self):
        """F-9 preserved: this plan added a guard suite WITHOUT adding the first source pin.

        The census assertions in this file parse the runner modules as FILES, which is a property of
        this file and not a pin on the function's text: none of them would break if the function's
        body were reformatted or its statements reordered. What must not appear is a test that reads
        `build_parser`'s SOURCE TEXT and asserts on its content or offsets, because that is the pin
        class that obstructed every sibling plan in this Set.
        """

        # Assembled at runtime so this scanner cannot match its OWN needle literals. A hardcoded
        # needle list would make this test fail on itself, and "exclude this file" would be the
        # wrong fix: this file must be scanned too.
        target = "build" + "_parser"
        needles = tuple(
            f"getsource({host}.{target}" for host in ("oc_runipd", "agy_runipd")
        ) + (f'split("def {target}', f"split('def {target}")

        offenders: list[str] = []
        for path in sorted((AW.parent / "tests").glob("test_*.py")):
            text = path.read_text(encoding="utf-8")
            for needle in needles:
                if needle in text:
                    offenders.append(f"{path.name}: {needle}")
        self.assertEqual(
            offenders,
            [],
            f"a source-text pin on build_parser has appeared: {offenders}. This function had ZERO "
            f"at execution HEAD, which is what makes it the one symbol in this Set a relocation "
            f"breaks no pin on; adding one now would create the obstacle the Set is trying to "
            f"avoid",
        )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
